import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(storage_dir=tmp_path / "uploads")


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


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


# Test levels used by the Unit Test Report and the System Validation Report (docs/). A file is a system
# test file when its tests go through the whole HTTP API, start a real server, or run a real model in a
# child process; everything else tests one component on its own.
SYSTEM_TEST_FILES = {
    "test_acceptance.py",
    "test_ack_time.py",
    "test_api_download.py",
    "test_api_status.py",
    "test_api_submit.py",
    "test_app.py",
    "test_demo_script.py",
    "test_determinism.py",
    "test_edge_case_inputs.py",
    "test_evaluation_limits.py",
    "test_evaluation_runner.py",
    "test_failure_paths.py",
    "test_memory_limit.py",
    "test_openapi.py",
}


def pytest_collection_modifyitems(items):
    for item in items:
        level = pytest.mark.system if item.path.name in SYSTEM_TEST_FILES else pytest.mark.unit
        item.add_marker(level)
