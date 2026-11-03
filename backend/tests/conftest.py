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
