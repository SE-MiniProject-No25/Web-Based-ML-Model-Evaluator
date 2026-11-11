"""The memory limit on Windows: a job object around the evaluation process (TEST-10, TC-15, DEF-04).

Linux and macOS are covered by ``test_evaluation_limits.py`` (the worker limits itself there).
"""

import subprocess
import sys

import pytest

from app.config import Settings
from app.evaluation import run_evaluation
from app.results import ResultService, Status
from app.security import limit_child_memory
from tests.helpers import write_classification_fixture
from tests.slow_models import SixHundredMegabyteModel

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="job objects exist on Windows only")
MB = 1024 * 1024


def evaluate_hungry_model(tmp_path, limit_bytes):
    import joblib

    _, data = write_classification_fixture(tmp_path)
    model = tmp_path / "hungry.joblib"
    joblib.dump(SixHundredMegabyteModel(), model)
    service = ResultService()
    evaluation = service.create("classification", "label", "m", "d", model_path=model, dataset_path=data)
    settings = Settings(evaluation_memory_limit_bytes=limit_bytes, evaluation_timeout_seconds=60)
    run_evaluation(evaluation.id, service, metrics_fn=lambda *_: {"accuracy": 1.0}, settings=settings)
    return service.get(evaluation.id)


@windows_only
def test_a_model_over_the_limit_is_stopped_on_windows(tmp_path):
    evaluation = evaluate_hungry_model(tmp_path, 300 * MB)

    assert evaluation.status is Status.FAILED
    assert evaluation.error["code"] == "RESOURCE_LIMIT_EXCEEDED"
    assert "memory limit" in evaluation.error["message"]


@windows_only
def test_the_same_model_runs_when_the_limit_allows_it(tmp_path):
    """So the failure above is the limit, not the model."""
    assert evaluate_hungry_model(tmp_path, 2048 * MB).status is Status.COMPLETED


@windows_only
def test_closing_the_limit_ends_a_child_that_is_still_running():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        limit = limit_child_memory(child, 512 * MB)
        assert limit is not None
        limit.close()
        child.wait(timeout=10)  # would raise: the child sleeps for 60 s unless the job ends it on close
        limit.close()  # closing twice is harmless
    finally:
        if child.poll() is None:
            child.kill()


def test_no_limit_is_applied_for_zero_or_on_other_platforms(monkeypatch):
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert limit_child_memory(child, 0) is None
    monkeypatch.setattr(sys, "platform", "linux")
    assert limit_child_memory(child, 512 * MB) is None
