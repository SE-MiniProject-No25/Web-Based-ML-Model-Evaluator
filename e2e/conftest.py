"""Starts the real backend and frontend for the end-to-end browser tests (TEST-07).

Each test run gets its own backend (a free port and an empty storage folder) and its own Vite dev
server, whose ``/api`` proxy points at that backend. Nothing already running on 8000 or 5173 is used.
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
DEMO_INPUTS = REPO / "deliverable-2" / "demo-inputs"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until_up(url: str, process: subprocess.Popen, what: str, seconds: float = 60) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"the {what} exited while starting")
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"the {what} did not start within {seconds:.0f} s")


def stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        if sys.platform == "win32":  # npm starts node as a child: end the whole tree
            kill_tree = ["taskkill", "/F", "/T", "/PID", str(process.pid)]
            subprocess.run(kill_tree, capture_output=True, check=False)
        else:
            process.terminate()
        process.wait(timeout=20)


@pytest.fixture(scope="session")
def app_url():
    """The frontend URL, with a backend behind it."""
    api_port, ui_port = free_port(), free_port()
    storage = tempfile.mkdtemp(prefix="e2e-uploads-")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(api_port), "--log-level", "warning"],
        cwd=REPO / "backend",
        env={**os.environ, "MLEVAL_STORAGE_DIR": storage},
    )
    npm = shutil.which("npm")
    frontend = subprocess.Popen(
        [npm, "run", "dev", "--", "--port", str(ui_port), "--strictPort"],
        cwd=REPO / "frontend",
        env={**os.environ, "VITE_API_TARGET": f"http://127.0.0.1:{api_port}"},
        stdout=subprocess.DEVNULL,
    )
    try:
        wait_until_up(f"http://127.0.0.1:{api_port}/api/health", backend, "backend")
        wait_until_up(f"http://localhost:{ui_port}/", frontend, "frontend")
        yield f"http://localhost:{ui_port}"
    finally:
        stop(frontend)
        stop(backend)
        shutil.rmtree(storage, ignore_errors=True)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        # For example "msedge"; by default Playwright's own Chromium.
        channel = os.environ.get("E2E_BROWSER_CHANNEL") or None
        browser = p.chromium.launch(channel=channel)
        yield browser
        browser.close()


@pytest.fixture
def page(browser, app_url, tmp_path):
    context = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.set_default_timeout(30_000)
    page.goto(app_url)
    yield page
    context.close()
