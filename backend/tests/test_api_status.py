import pytest
from fastapi.testclient import TestClient

from app.errors import ErrorCode
from app.main import create_app
from app.results import ResultService, Status, format_status
from tests.helpers import write_classification_fixture, write_regression_fixture


@pytest.fixture
def results():
    return ResultService()


@pytest.fixture
def client(settings, results):
    return TestClient(create_app(settings, results))


def submit(client, model, data, **form):
    fields = {"task_type": "classification", "target_column": "label", **form}
    files = {"model": (model.name, model.read_bytes()), "dataset": (data.name, data.read_bytes())}
    return client.post("/api/evaluations", data=fields, files=files).json()["evaluation_id"]


def test_pending_and_running_report_only_id_and_status(client, results):
    evaluation = results.create("classification", "label", "m.joblib", "d.csv")
    assert client.get(f"/api/evaluations/{evaluation.id}").json() == {
        "evaluation_id": evaluation.id,
        "status": "pending",
    }
    results.mark_running(evaluation.id)
    assert client.get(f"/api/evaluations/{evaluation.id}").json() == {
        "evaluation_id": evaluation.id,
        "status": "running",
    }


def test_status_follows_the_lifecycle_to_completed(client, results):
    """TC-10: status moves through the defined lifecycle and the result is available."""
    evaluation = results.create("classification", "label", "m.joblib", "d.csv")
    seen = [client.get(f"/api/evaluations/{evaluation.id}").json()["status"]]
    results.mark_running(evaluation.id)
    seen.append(client.get(f"/api/evaluations/{evaluation.id}").json()["status"])
    results.mark_completed(evaluation.id, {"accuracy": 0.94, "f1": 0.925})
    body = client.get(f"/api/evaluations/{evaluation.id}").json()
    seen.append(body["status"])

    assert seen == ["pending", "running", "completed"]
    assert body == {
        "evaluation_id": evaluation.id,
        "status": "completed",
        "task_type": "classification",
        "metrics": {"accuracy": 0.94, "f1": 0.925},
    }


def test_failed_evaluation_returns_the_error_object_instead_of_metrics(client, results):
    evaluation = results.create("classification", "label", "m.joblib", "d.csv")
    results.mark_running(evaluation.id)
    results.mark_failed(evaluation.id, ErrorCode.INCOMPATIBLE_INPUTS, "The dataset features do not match.")
    body = client.get(f"/api/evaluations/{evaluation.id}").json()
    assert body == {
        "evaluation_id": evaluation.id,
        "status": "failed",
        "task_type": "classification",
        "error": {"code": "INCOMPATIBLE_INPUTS", "message": "The dataset features do not match."},
    }
    assert "metrics" not in body


def test_unknown_id_is_a_404_with_the_standard_error(client):
    """TC-24 (status half) / FR-19."""
    response = client.get("/api/evaluations/00000000-0000-4000-8000-000000000000")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "EVALUATION_NOT_FOUND", "message": "Evaluation not found."}}


def test_end_to_end_submit_then_read_the_result(client, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation_id = submit(client, model, data)
    body = client.get(f"/api/evaluations/{evaluation_id}").json()
    assert body["evaluation_id"] == evaluation_id
    assert body["status"] == "completed"
    assert body["task_type"] == "classification"
    assert "metrics" in body


def test_end_to_end_regression(client, tmp_path):
    model, data = write_regression_fixture(tmp_path)
    evaluation_id = submit(client, model, data, task_type="regression", target_column="price")
    assert client.get(f"/api/evaluations/{evaluation_id}").json()["status"] == "completed"


def test_end_to_end_incompatible_inputs_end_failed_without_leaking_details(client, tmp_path):
    model, _ = write_classification_fixture(tmp_path / "c")
    _, wrong_data = write_regression_fixture(tmp_path / "r", target="label")
    evaluation_id = submit(client, model, wrong_data)
    body = client.get(f"/api/evaluations/{evaluation_id}").json()
    assert body["status"] == "failed"
    assert set(body["error"]) == {"code", "message"}
    assert str(tmp_path) not in body["error"]["message"]
    assert "metrics" not in body


def test_status_response_never_includes_paths_or_filenames(results):
    evaluation = results.create(
        "regression", "price", "secret-name.joblib", "private.csv", model_path="/srv/x", dataset_path="/srv/y"
    )
    results.mark_running(evaluation.id)
    done = results.mark_completed(evaluation.id, {"mae": 1.0})
    text = str(format_status(done))
    assert "/srv" not in text and "secret-name" not in text and "private" not in text
    assert done.status is Status.COMPLETED
