"""US-04: incompatible inputs (TC-11), time and memory limits (TC-15), safe failures (TC-16, runtime half)."""

import logging
import time

import joblib
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import ErrorCode
from app.evaluation import run_evaluation
from app.evaluation.runner import GENERIC_FAILURE_MESSAGE, _incompatible_message
from app.main import create_app
from app.results import ResultService, Status
from tests.helpers import write_classification_fixture, write_regression_fixture
from tests.slow_models import (
    ChattyModel,
    CountOnlyModel,
    EnvProbeModel,
    ExplodingModel,
    MemoryHogModel,
    SleepyModel,
)


@pytest.fixture
def service():
    return ResultService()


def submit(service, model_path, data_path, target="label", task="classification"):
    return service.create(task, target, "m.joblib", "d.csv", model_path=model_path, dataset_path=data_path)


def custom_model(tmp_path, model):
    """A dataset with the standard columns (a, b, label) and a custom model for it."""
    _, data = write_classification_fixture(tmp_path)
    path = tmp_path / "custom.joblib"
    joblib.dump(model, path)
    return path, data


def failed_error(service, evaluation_id):
    evaluation = service.get(evaluation_id)
    assert evaluation.status is Status.FAILED, evaluation
    return evaluation.error


# --- TC-11: incompatible model / dataset pairs ------------------------------------------------


def test_feature_mismatch_ends_as_incompatible_inputs(service, tmp_path):
    model, _ = write_classification_fixture(tmp_path / "c")  # trained on a, b
    _, other = write_regression_fixture(tmp_path / "r", target="label")  # columns x1, x2, label
    evaluation = submit(service, model, other)

    run_evaluation(evaluation.id, service)

    error = failed_error(service, evaluation.id)
    assert error["code"] == "INCOMPATIBLE_INPUTS"
    assert "Missing from the dataset: a, b." in error["message"]
    assert "Not used by the model: x1, x2." in error["message"]
    assert str(tmp_path) not in error["message"]


def test_choosing_a_feature_as_the_target_is_explained(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)  # features a, b; target label
    evaluation = submit(service, model, data, target="a")  # wrong target picked

    run_evaluation(evaluation.id, service)

    error = failed_error(service, evaluation.id)
    assert error["code"] == "INCOMPATIBLE_INPUTS"
    assert "Missing from the dataset: a." in error["message"]
    assert "Not used by the model: label." in error["message"]


def test_feature_count_mismatch_without_names_is_reported_with_counts(service, tmp_path):
    model_path, _ = custom_model(tmp_path, CountOnlyModel())  # expects 2 features
    three_features = tmp_path / "three.csv"
    three_features.write_text("a,b,c,label\n1,2,3,0\n4,5,6,1\n")
    evaluation = submit(service, model_path, three_features)

    run_evaluation(evaluation.id, service)

    error = failed_error(service, evaluation.id)
    assert error["code"] == "INCOMPATIBLE_INPUTS"
    assert "3 feature column(s)" in error["message"] and "expects 2" in error["message"]


def test_columns_in_a_different_order_still_evaluate(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    reordered = tmp_path / "reordered.csv"
    lines = data.read_text().splitlines()
    reordered.write_text("\n".join(",".join(reversed(line.split(","))) for line in lines) + "\n")  # label,b,a
    evaluation = submit(service, model, reordered)

    run_evaluation(evaluation.id, service)

    assert service.get(evaluation.id).status is Status.COMPLETED


def test_long_column_lists_are_shortened():
    message = _incompatible_message({"missing": [f"column_{i}" for i in range(9)], "extra": ["x" * 200]})
    assert "column_0, column_1, column_2, column_3, column_4…" in message
    assert "column_5" not in message
    assert "x" * 51 not in message


# --- TC-15: time and memory limits --------------------------------------------------------------


def test_exceeding_the_time_limit_stops_the_evaluation(service, tmp_path):
    model, data = custom_model(tmp_path, SleepyModel())
    evaluation = submit(service, model, data)

    started = time.monotonic()
    run_evaluation(evaluation.id, service, settings=Settings(evaluation_timeout_seconds=3))
    elapsed = time.monotonic() - started

    error = failed_error(service, evaluation.id)
    assert error["code"] == "RESOURCE_LIMIT_EXCEEDED"
    assert "time limit of 3 seconds" in error["message"]
    assert elapsed < 30, "the model sleeps for 60 s, so the child must have been killed"


def test_exceeding_the_memory_limit_stops_the_evaluation(service, tmp_path):
    """Enforced by the worker on Linux and macOS, and by a job object on Windows (TEST-10)."""
    model, data = custom_model(tmp_path, MemoryHogModel())
    evaluation = submit(service, model, data)

    run_evaluation(
        evaluation.id,
        service,
        settings=Settings(evaluation_memory_limit_bytes=1024 * 1024 * 1024, evaluation_timeout_seconds=60),
    )

    error = failed_error(service, evaluation.id)
    assert error["code"] == "RESOURCE_LIMIT_EXCEEDED"
    assert "memory limit" in error["message"]


# --- everything else: safe, generic failures ----------------------------------------------------


def test_a_crashing_model_fails_with_a_generic_message_and_logs_the_traceback(service, tmp_path, caplog):
    model, data = custom_model(tmp_path, ExplodingModel())
    evaluation = submit(service, model, data)

    with caplog.at_level(logging.ERROR):
        run_evaluation(evaluation.id, service)

    error = failed_error(service, evaluation.id)
    assert error == {"code": "EVALUATION_FAILED", "message": GENERIC_FAILURE_MESSAGE}
    assert "secret" not in str(error) and "/srv" not in str(error)
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "secret internal detail" in logged  # kept server-side for diagnosis


def test_a_model_that_prints_does_not_disturb_the_result(service, tmp_path):
    model, data = custom_model(tmp_path, ChattyModel())
    evaluation = submit(service, model, data)
    seen = {}

    def metrics_fn(task_type, y_true, y_pred):
        seen["pred"] = list(y_pred)
        return {"ok": 1.0}

    run_evaluation(evaluation.id, service, metrics_fn=metrics_fn)

    assert service.get(evaluation.id).status is Status.COMPLETED
    assert set(seen["pred"]) == {1}


def test_server_secrets_are_not_visible_to_the_model(service, tmp_path, monkeypatch):
    monkeypatch.setenv("MLEVAL_TEST_SECRET", "hunter2")
    model, data = custom_model(tmp_path, EnvProbeModel())
    evaluation = submit(service, model, data)
    seen = {}

    def metrics_fn(task_type, y_true, y_pred):
        seen["visible"] = np.asarray(y_pred).max()
        return {}

    run_evaluation(evaluation.id, service, metrics_fn=metrics_fn)

    assert service.get(evaluation.id).status is Status.COMPLETED
    assert seen["visible"] == 0


# --- end to end through the API -----------------------------------------------------------------


def post(client, model_path, data_path, task="classification", target="label"):
    response = client.post(
        "/api/evaluations",
        data={"task_type": task, "target_column": target},
        files={
            "model": (model_path.name, model_path.read_bytes()),
            "dataset": (data_path.name, data_path.read_bytes()),
        },
    )
    assert response.status_code == 202, response.text
    return response.json()["evaluation_id"]


def test_api_reports_incompatible_inputs_to_the_client(tmp_path):
    client = TestClient(create_app(Settings(storage_dir=tmp_path / "up")))
    model, _ = write_classification_fixture(tmp_path / "c")
    _, other = write_regression_fixture(tmp_path / "r", target="label")

    body = client.get(f"/api/evaluations/{post(client, model, other)}").json()

    assert body["status"] == "failed"
    assert body["error"]["code"] == "INCOMPATIBLE_INPUTS"
    assert "Missing from the dataset: a, b." in body["error"]["message"]
    assert "metrics" not in body


def test_api_stops_an_evaluation_that_exceeds_the_time_limit(tmp_path):
    settings = Settings(storage_dir=tmp_path / "up", evaluation_timeout_seconds=3)
    client = TestClient(create_app(settings))
    model, data = custom_model(tmp_path, SleepyModel())

    body = client.get(f"/api/evaluations/{post(client, model, data)}").json()

    assert body["status"] == "failed"
    assert body["error"]["code"] == ErrorCode.RESOURCE_LIMIT_EXCEEDED.value
