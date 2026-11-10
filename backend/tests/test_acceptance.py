"""End-to-end acceptance checks against the EN-02 reference fixtures (TC-08, TC-09).

Unit tests already check the metric formulas; these run the whole path (upload, validation, isolated
model run, metrics, result) through the API and compare with the expected values.
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


def run_reference(client, folder, task_type, target):
    base = FIXTURES / folder
    response = client.post(
        "/api/evaluations",
        data={"task_type": task_type, "target_column": target},
        files={
            "model": ("model.joblib", (base / "model.joblib").read_bytes()),
            "dataset": ("data.csv", (base / "data.csv").read_bytes()),
        },
    )
    assert response.status_code == 202, response.text
    body = client.get(f"/api/evaluations/{response.json()['evaluation_id']}").json()
    expected = json.loads((base / "expected_metrics.json").read_text())
    return body, expected


def test_classification_reference_pair_reports_the_expected_metrics(client):
    """TC-08: accuracy, precision, recall and F1 are reported and match the known values."""
    body, expected = run_reference(client, "classification", "classification", "label")

    assert body["status"] == "completed"
    assert body["task_type"] == "classification"
    assert set(expected) <= set(body["metrics"]) >= {"accuracy", "precision", "recall", "f1"}
    assert body["metrics"] == pytest.approx(expected)


def test_regression_reference_pair_reports_the_expected_metrics(client):
    """TC-09: MAE, MSE, RMSE and R² are reported and match the known values."""
    body, expected = run_reference(client, "regression", "regression", "price")

    assert body["status"] == "completed"
    assert body["task_type"] == "regression"
    assert set(expected) <= set(body["metrics"]) >= {"mae", "mse", "rmse", "r2"}
    assert body["metrics"] == pytest.approx(expected)
