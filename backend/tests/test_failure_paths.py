"""System-level failure paths that were not exercised before: the model worker dying without reporting,
and an upload that fails halfway through being stored."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import ErrorCode
from app.evaluation import run_evaluation
from app.evaluation import runner as runner_module
from app.evaluation.runner import GENERIC_FAILURE_MESSAGE, _failure_from, _incompatible_message
from app.main import create_app
from app.results import ResultService, Status
from tests.helpers import write_classification_fixture

FIXTURES = Path(__file__).parent / "fixtures" / "classification"


# --- the worker process ---------------------------------------------------------------------------


def test_a_worker_that_dies_without_a_result_fails_the_evaluation_safely(monkeypatch, tmp_path, caplog):
    """e.g. killed by the operating system for using too much memory: there is no result file."""
    crashing = tmp_path / "crashing_worker.py"
    crashing.write_text("import sys\nsys.exit(3)\n")
    monkeypatch.setattr(runner_module, "WORKER_PATH", crashing)
    model, data = write_classification_fixture(tmp_path)
    service = ResultService()
    evaluation = service.create("classification", "label", "m", "d", model_path=model, dataset_path=data)

    with caplog.at_level(logging.ERROR):
        run_evaluation(evaluation.id, service)

    failed = service.get(evaluation.id)
    assert failed.status is Status.FAILED
    assert failed.error == {"code": "EVALUATION_FAILED", "message": GENERIC_FAILURE_MESSAGE}
    assert "without a result" in " ".join(r.getMessage() for r in caplog.records)  # logged for the operator


def test_the_workers_memory_limit_report_becomes_a_resource_limit_failure():
    failure = _failure_from({"ok": False, "code": "RESOURCE_LIMIT_EXCEEDED", "reason": "memory"})
    assert failure.code is ErrorCode.RESOURCE_LIMIT_EXCEEDED
    assert "memory limit" in failure.message


@pytest.mark.parametrize("report", [{"ok": False}, {"ok": False, "code": "SOMETHING_NEW"}, {"code": None}])
def test_an_unrecognised_worker_report_is_a_generic_failure(report):
    """Anything the worker says that the runner does not recognise is never shown to the user."""
    failure = _failure_from(report)
    assert (failure.code, failure.message) == (ErrorCode.EVALUATION_FAILED, GENERIC_FAILURE_MESSAGE)


def test_a_mismatch_message_only_lists_what_is_there():
    message = _incompatible_message({"missing": ["a"], "extra": []})
    assert "Missing from the dataset: a." in message
    assert "Not used by the model" not in message


# --- an upload that fails halfway -------------------------------------------------------------------


def test_a_failed_second_save_removes_the_first_file_and_creates_no_evaluation(tmp_path):
    settings = Settings(storage_dir=tmp_path / "uploads")
    results = ResultService()
    app = create_app(settings, results)
    save = app.state.storage.save
    calls = []

    def flaky_save(data, extension):
        calls.append(extension)
        if len(calls) == 2:  # the dataset, after the model was stored
            raise OSError("disk full at /srv/secret/path")
        return save(data, extension)

    app.state.storage.save = flaky_save
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", (FIXTURES / "model.joblib").read_bytes()),
            "dataset": ("data.csv", (FIXTURES / "data.csv").read_bytes()),
        },
    )

    assert response.status_code == 500
    assert "disk full" not in response.text and "/srv" not in response.text  # nothing internal leaks
    assert list(settings.storage_dir.iterdir()) == [], "the model saved first must not be left behind"
