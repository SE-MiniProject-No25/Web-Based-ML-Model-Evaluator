"""When the retention cleanup runs, and what it keeps (TEST-05, TC-18, DEF-02, DEF-10).

Expired uploads are removed at start-up and on a timer, without waiting for a new submission, and the
files of an evaluation that is still pending or running are never removed, however old they are.
"""

import os
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.retention import sweep_expired_artifacts
from app.config import Settings
from app.errors import ErrorCode
from app.main import create_app
from app.results import ResultService
from tests.helpers import write_classification_fixture

HOUR = 3600


def old_file(directory: Path, name: str, age_seconds: float) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(b"x")
    then = time.time() - age_seconds
    os.utime(path, (then, then))
    return path


def make_app(tmp_path, **overrides):
    settings = Settings(storage_dir=tmp_path / "uploads", **overrides)
    return create_app(settings), settings.storage_dir


def test_unfinished_evaluations_report_their_files_and_finished_ones_do_not(tmp_path):
    results = ResultService()
    pending = results.create("classification", "y", "m", "d", tmp_path / "p.joblib", tmp_path / "p.csv")
    running = results.create("classification", "y", "m", "d", tmp_path / "r.joblib", tmp_path / "r.csv")
    done = results.create("classification", "y", "m", "d", tmp_path / "c.joblib", tmp_path / "c.csv")
    results.create("classification", "y", "m", "d")  # no stored files
    results.mark_running(running.id)
    results.mark_running(done.id)
    results.mark_completed(done.id, {"accuracy": 1.0})

    assert sorted(p.name for p in results.active_paths()) == ["p.csv", "p.joblib", "r.csv", "r.joblib"]
    assert pending.status.value == "pending"


def test_the_sweep_keeps_the_files_of_a_running_evaluation_and_removes_finished_ones(tmp_path):
    """DEF-10: a retention shorter than an evaluation could delete its files while it ran."""
    app, storage = make_app(tmp_path, retention_seconds=60)
    results = app.state.results
    running_files = [old_file(storage, "run.joblib", 2 * HOUR), old_file(storage, "run.csv", 2 * HOUR)]
    finished_files = [old_file(storage, "done.joblib", 2 * HOUR), old_file(storage, "done.csv", 2 * HOUR)]
    fresh = old_file(storage, "fresh.csv", 1)
    running = results.create("classification", "y", "m", "d", *running_files)
    results.mark_running(running.id)
    done = results.create("classification", "y", "m", "d", *finished_files)
    results.mark_running(done.id)
    results.mark_failed(done.id, ErrorCode.EVALUATION_FAILED, "x")

    sweep_expired_artifacts(app.state)

    assert all(p.exists() for p in running_files)  # older than the retention period, but still in use
    assert not any(p.exists() for p in finished_files)
    assert fresh.exists()  # not expired yet

    results.mark_completed(running.id, {"accuracy": 1.0})
    sweep_expired_artifacts(app.state)
    assert not any(p.exists() for p in running_files)  # removed once the evaluation has finished


def test_expired_files_are_removed_at_start_up_without_any_request(tmp_path):
    """DEF-02: expired uploads used to stay until the next submission."""
    app, storage = make_app(tmp_path, retention_seconds=HOUR, cleanup_interval_seconds=0)
    stale = old_file(storage, "left-over-from-last-run.joblib", 2 * HOUR)

    with TestClient(app):
        assert not stale.exists()


def test_expired_files_are_removed_on_a_timer_without_any_request(tmp_path):
    app, storage = make_app(tmp_path, retention_seconds=1, cleanup_interval_seconds=1)

    with TestClient(app):
        upload = old_file(storage, "uploaded-just-now.csv", 0)
        deadline = time.monotonic() + 10
        while upload.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not upload.exists()


def test_a_failing_sweep_is_logged_and_does_not_stop_the_service(tmp_path, caplog):
    app, _ = make_app(tmp_path, cleanup_interval_seconds=0)

    def broken(**_):
        raise OSError("disk unavailable")

    app.state.storage.cleanup_expired = broken
    with TestClient(app) as client:  # the start-up sweep fails
        assert client.get("/api/health").status_code == 200
    assert "Retention cleanup failed" in caplog.text


def test_a_submission_sweeps_but_keeps_the_files_of_another_unfinished_evaluation(tmp_path):
    app, storage = make_app(tmp_path, retention_seconds=60)
    client = TestClient(app)
    waiting = [old_file(storage, "waiting.joblib", 2 * HOUR), old_file(storage, "waiting.csv", 2 * HOUR)]
    app.state.results.create("classification", "label", "m", "d", *waiting)  # still pending
    stale = old_file(storage, "stale.csv", 2 * HOUR)
    model, data = write_classification_fixture(tmp_path / "fixture")

    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={"model": ("m.joblib", model.read_bytes()), "dataset": ("d.csv", data.read_bytes())},
    )

    assert response.status_code == 202
    assert all(p.exists() for p in waiting)
    assert not stale.exists()


def test_the_cleanup_interval_can_be_set_from_the_environment(monkeypatch):
    from app.config import load_settings

    monkeypatch.setenv("MLEVAL_CLEANUP_INTERVAL_SECONDS", "42")
    assert load_settings().cleanup_interval_seconds == 42
