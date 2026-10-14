import logging

import pytest

from app.errors import ErrorCode
from app.evaluation import run_evaluation
from app.evaluation.runner import GENERIC_FAILURE_MESSAGE
from app.results import InvalidTransition, ResultService, Status
from tests.helpers import write_classification_fixture, write_regression_fixture


@pytest.fixture
def service():
    return ResultService()


def submit(service, task_type, model_path, dataset_path, target):
    return service.create(
        task_type, target, "model.joblib", "data.csv", model_path=model_path, dataset_path=dataset_path
    )


def test_classification_run_completes_with_metrics(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "label")
    calls = []

    def fake_metrics(task_type, y_true, y_pred):
        calls.append((task_type, list(y_true), list(y_pred)))
        return {"accuracy": 1.0}

    run_evaluation(evaluation.id, service, metrics_fn=fake_metrics)

    done = service.get(evaluation.id)
    assert done.status is Status.COMPLETED
    assert done.metrics == {"accuracy": 1.0}
    assert done.finished_at is not None
    ((task_type, y_true, y_pred),) = calls
    assert task_type == "classification"
    assert len(y_true) == len(y_pred) == 60
    # Predictions are for the dataset rows with the target column removed.
    assert set(y_pred) <= {0, 1}


def test_regression_run_completes(service, tmp_path):
    model, data = write_regression_fixture(tmp_path)
    evaluation = submit(service, "regression", model, data, "price")
    seen = {}

    def fake_metrics(task_type, y_true, y_pred):
        seen["max_error"] = float(abs(y_true - y_pred).max())
        return {"mae": 0.0}

    run_evaluation(evaluation.id, service, metrics_fn=fake_metrics)

    assert service.get(evaluation.id).status is Status.COMPLETED
    assert seen["max_error"] < 1e-6  # the linear model reproduces its own training data


def test_default_metrics_stub_is_used_until_the_metrics_service_lands(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "label")
    run_evaluation(evaluation.id, service)
    assert service.get(evaluation.id).metrics == {"samples": 60}


def test_status_is_running_while_the_model_executes(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "label")
    observed = []

    def metrics_fn(task_type, y_true, y_pred):
        observed.append(service.get(evaluation.id).status)
        return {}

    run_evaluation(evaluation.id, service, metrics_fn=metrics_fn)
    assert observed == [Status.RUNNING]


def assert_failed_safely(service, evaluation_id, tmp_path):
    failed = service.get(evaluation_id)
    assert failed.status is Status.FAILED
    assert failed.metrics is None
    assert failed.error == {"code": ErrorCode.EVALUATION_FAILED.value, "message": GENERIC_FAILURE_MESSAGE}
    assert str(tmp_path) not in failed.error["message"]


def test_dataset_that_does_not_match_the_model_fails_safely(service, tmp_path):
    model, _ = write_classification_fixture(tmp_path / "c")
    _, other_data = write_regression_fixture(tmp_path / "r", target="label")  # wrong feature columns
    evaluation = submit(service, "classification", model, other_data, "label")
    run_evaluation(evaluation.id, service)
    assert_failed_safely(service, evaluation.id, tmp_path)


def test_corrupt_model_file_fails_safely(service, tmp_path):
    _, data = write_classification_fixture(tmp_path)
    bad_model = tmp_path / "bad.joblib"
    bad_model.write_bytes(b"not a model")
    evaluation = submit(service, "classification", bad_model, data, "label")
    run_evaluation(evaluation.id, service)
    assert_failed_safely(service, evaluation.id, tmp_path)


def test_missing_target_column_fails_safely(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "no_such_column")
    run_evaluation(evaluation.id, service)
    assert_failed_safely(service, evaluation.id, tmp_path)


def test_a_failing_metrics_call_fails_the_evaluation(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "label")

    def broken(*_):
        raise RuntimeError("secret internal detail")

    run_evaluation(evaluation.id, service, metrics_fn=broken)
    assert_failed_safely(service, evaluation.id, tmp_path)
    assert "secret" not in service.get(evaluation.id).error["message"]


def test_diagnostics_are_logged_server_side(service, tmp_path, caplog):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "no_such_column")
    with caplog.at_level(logging.ERROR):
        run_evaluation(evaluation.id, service)
    assert any(evaluation.id in r.getMessage() and r.exc_info for r in caplog.records)


def test_an_evaluation_cannot_be_run_twice(service, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation = submit(service, "classification", model, data, "label")
    run_evaluation(evaluation.id, service)
    with pytest.raises(InvalidTransition):
        run_evaluation(evaluation.id, service)
    assert service.get(evaluation.id).status is Status.COMPLETED
