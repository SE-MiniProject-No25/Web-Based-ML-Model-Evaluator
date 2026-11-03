
"""API-level determinism tests for repeated model evaluations.

TC-20 / NFR-03:
The same model, dataset, and configuration must produce
identical evaluation metrics across three submissions.
"""

import pytest

from tests.helpers import write_classification_fixture, write_regression_fixture


@pytest.mark.parametrize(
    ("task_type", "target_column", "fixture_writer"),
    [
        ("classification", "label", write_classification_fixture),
        ("regression", "price", write_regression_fixture),
    ],
)
def test_repeated_evaluations_produce_identical_metrics(
    client,
    tmp_path,
    task_type,
    target_column,
    fixture_writer,
):
    """TC-20: Three identical API submissions produce identical metrics."""

    model_path, dataset_path = fixture_writer(tmp_path)

    evaluation_ids = []
    results = []

    for _ in range(3):
        response = client.post(
            "/api/evaluations",
            data={
                "task_type": task_type,
                "target_column": target_column,
            },
            files={
                "model": (model_path.name, model_path.read_bytes()),
                "dataset": (dataset_path.name, dataset_path.read_bytes()),
            },
        )

        assert response.status_code == 202

        evaluation_id = response.json()["evaluation_id"]
        evaluation_ids.append(evaluation_id)

        result_response = client.get(
            f"/api/evaluations/{evaluation_id}"
        )

        assert result_response.status_code == 200

        result = result_response.json()

        assert result["status"] == "completed"
        assert result["task_type"] == task_type
        assert result["metrics"] is not None

        results.append(result["metrics"])

    # Each submission must create a separate evaluation.
    assert len(set(evaluation_ids)) == 3

    # All three evaluations must produce exactly the same metrics.
    assert results[0] == results[1] == results[2]
