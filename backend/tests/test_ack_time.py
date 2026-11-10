"""TC-19 / NFR-02: a valid evaluation is acknowledged within 2 seconds.

Uses a real server in a subprocess: the test client waits for background tasks before it returns, so
it cannot tell when the 202 was actually sent.
"""

import time
from pathlib import Path

import httpx

from scripts.measure_ack_time import DEFAULT_LIMIT_SECONDS, format_report, measure

BACKEND_DIR = Path(__file__).resolve().parents[1]


def test_ten_valid_requests_are_each_acknowledged_within_two_seconds(server_url):
    times = measure(server_url, runs=10)

    report = format_report(times, DEFAULT_LIMIT_SECONDS)
    assert len(times) == 10
    assert all(t < DEFAULT_LIMIT_SECONDS for t in times), f"acknowledgement too slow:\n{report}"
    print(report)  # visible with `pytest -s`; the Test Report records these numbers


def test_the_acknowledgement_does_not_wait_for_the_evaluation(server_url):
    """The evaluation (model execution and metrics) runs after the 202, not before it."""
    model = (BACKEND_DIR / "tests" / "fixtures" / "classification" / "model.joblib").read_bytes()
    data = (BACKEND_DIR / "tests" / "fixtures" / "classification" / "data.csv").read_bytes()
    with httpx.Client(base_url=server_url, timeout=30) as client:
        response = client.post(
            "/api/evaluations",
            data={"task_type": "classification", "target_column": "label"},
            files={"model": ("model.joblib", model), "dataset": ("data.csv", data)},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "pending"  # not completed: it had not run yet
        evaluation_id = response.json()["evaluation_id"]

        # ...and it does finish afterwards.
        deadline = time.monotonic() + 30
        status = "pending"
        while status in {"pending", "running"} and time.monotonic() < deadline:
            time.sleep(0.3)
            status = client.get(f"/api/evaluations/{evaluation_id}").json()["status"]
        assert status == "completed"
