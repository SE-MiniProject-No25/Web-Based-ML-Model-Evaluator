"""GET /api/evaluations/{id}/download (US-03): TC-12, the download half of TC-24, and TC-25."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.errors import ErrorCode
from app.main import create_app
from app.results import ResultService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def results():
    return ResultService()


@pytest.fixture
def client(settings, results):
    return TestClient(create_app(settings, results))


def submit_reference_classification(client):
    folder = FIXTURES / "classification"
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", (folder / "model.joblib").read_bytes()),
            "dataset": ("data.csv", (folder / "data.csv").read_bytes()),
        },
    )
    assert response.status_code == 202
    return response.json()["evaluation_id"]


def test_completed_evaluation_downloads_as_a_json_attachment(client):
    """TC-12 / FR-15: a structured result file is returned."""
    evaluation_id = submit_reference_classification(client)
    response = client.get(f"/api/evaluations/{evaluation_id}/download")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    disposition = response.headers["content-disposition"]
    assert disposition == f'attachment; filename="evaluation-{evaluation_id}.json"'

    body = json.loads(response.content)
    assert body["evaluation_id"] == evaluation_id
    assert body["status"] == "completed"
    assert body["task_type"] == "classification"
    assert body["target_column"] == "label"
    assert body["model_filename"] == "model.joblib"
    assert body["dataset_filename"] == "data.csv"


def test_downloaded_metrics_match_the_reference_values(client):
    expected = json.loads((FIXTURES / "classification" / "expected_metrics.json").read_text())
    evaluation_id = submit_reference_classification(client)
    metrics = client.get(f"/api/evaluations/{evaluation_id}/download").json()["metrics"]
    assert metrics == pytest.approx(expected)


def test_download_includes_timestamps_in_order(client):
    evaluation_id = submit_reference_classification(client)
    body = client.get(f"/api/evaluations/{evaluation_id}/download").json()
    created = datetime.fromisoformat(body["created_at"])
    finished = datetime.fromisoformat(body["finished_at"])
    assert created.tzinfo is not None and finished >= created


def test_download_matches_the_status_endpoint(client):
    evaluation_id = submit_reference_classification(client)
    status = client.get(f"/api/evaluations/{evaluation_id}").json()
    download = client.get(f"/api/evaluations/{evaluation_id}/download").json()
    assert download["metrics"] == status["metrics"]
    assert download["task_type"] == status["task_type"]


def test_download_never_exposes_server_paths(client, settings):
    evaluation_id = submit_reference_classification(client)
    text = client.get(f"/api/evaluations/{evaluation_id}/download").text
    assert str(settings.storage_dir) not in text
    assert "model_path" not in text and "dataset_path" not in text


@pytest.mark.parametrize("advance", [None, "running"])
def test_download_before_completion_is_a_409_with_no_file(client, results, advance):
    """TC-25 / FR-20: pending and running evaluations cannot be downloaded."""
    evaluation = results.create("classification", "label", "m.joblib", "d.csv")
    if advance:
        results.mark_running(evaluation.id)

    response = client.get(f"/api/evaluations/{evaluation.id}/download")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == ErrorCode.EVALUATION_NOT_COMPLETED.value
    assert "content-disposition" not in response.headers
    assert "metrics" not in response.json()


def test_failed_evaluation_has_nothing_to_download(client, results):
    evaluation = results.create("classification", "label", "m.joblib", "d.csv")
    results.mark_running(evaluation.id)
    results.mark_failed(evaluation.id, ErrorCode.EVALUATION_FAILED, "x")

    response = client.get(f"/api/evaluations/{evaluation.id}/download")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EVALUATION_NOT_COMPLETED"
    assert "content-disposition" not in response.headers


def test_unknown_id_is_a_404(client):
    """TC-24 (download half) / FR-19."""
    response = client.get("/api/evaluations/00000000-0000-4000-8000-000000000000/download")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "EVALUATION_NOT_FOUND", "message": "Evaluation not found."}}
