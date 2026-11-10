"""TC-19 / NFR-02: a valid evaluation is acknowledged within 2 seconds.

Uses a real server in a subprocess: the test client waits for background tasks before it returns, so
it cannot tell when the 202 was actually sent.
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from scripts.measure_ack_time import DEFAULT_LIMIT_SECONDS, format_report, measure

BACKEND_DIR = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def server_url(tmp_path):
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=BACKEND_DIR,
        env={**os.environ, "MLEVAL_STORAGE_DIR": str(tmp_path / "uploads")},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                if httpx.get(f"{url}/api/health", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                pass
            if time.monotonic() > deadline or process.poll() is not None:
                raise RuntimeError("the test server did not start")
            time.sleep(0.2)
        yield url
    finally:
        process.kill()
        process.wait()


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
