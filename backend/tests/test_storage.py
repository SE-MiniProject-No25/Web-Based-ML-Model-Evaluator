"""Tests for Temporary Storage and Storage Lifecycle Manager (US-10, US-26, TC-13, TC-18).

Verifies that uploads are saved under server-generated UUID names in an isolated directory
outside the source tree, path-like filenames cannot control paths or write outside storage,
directory and file permissions are restrictive, and artifacts are cleaned up according to
the configured retention policy.
"""

import io
import os
import re
import stat
import time

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.storage import StorageLifecycleManager, TemporaryStorage
from tests.helpers import write_classification_fixture


def test_saved_files_get_server_generated_uuid_names(tmp_path):
    storage = TemporaryStorage(tmp_path)
    path = storage.save(b"a,b\n1,2\n", ".csv")
    assert re.fullmatch(r"[0-9a-f]{32}\.csv", path.name)
    assert path.read_bytes() == b"a,b\n1,2\n"
    assert path.parent.resolve() == tmp_path.resolve()


def test_streams_are_supported_and_names_are_unique(tmp_path):
    storage = TemporaryStorage(tmp_path)
    first = storage.save(io.BytesIO(b"x"), ".joblib")
    second = storage.save(io.BytesIO(b"x"), ".joblib")
    assert first != second
    assert first.exists()
    assert second.exists()


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "csv",
        "../x",
        ".c/sv",
        r"..\x",
        ".toolongextension",
        ".csv\x00.exe",
        ".",
        "...",
    ],
)
def test_user_controlled_extensions_cannot_alter_the_path(tmp_path, bad):
    storage = TemporaryStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.save(b"x", bad)


def test_delete_removes_stored_file_but_not_outside_files(tmp_path):
    storage = TemporaryStorage(tmp_path / "store")
    path = storage.save(b"x", ".csv")
    storage.delete(path)
    assert not path.exists()

    outside = tmp_path / "keep.txt"
    outside.write_text("keep")
    with pytest.raises(ValueError, match="outside the storage directory"):
        storage.delete(outside)
    assert outside.exists()


def test_delete_cannot_delete_storage_root_or_directories(tmp_path):
    storage = TemporaryStorage(tmp_path / "store")
    subdir = storage.root / "sub"
    subdir.mkdir()
    with pytest.raises(ValueError):
        storage.delete(subdir)
    assert subdir.exists()

    with pytest.raises(ValueError):
        storage.delete(storage.root)
    assert storage.root.exists()


def test_storage_directory_permissions_are_restrictive(tmp_path):
    """Architecture §6.1, AC 3: Temporary storage directory is restricted (0o700 on POSIX)."""
    store_dir = tmp_path / "secure_store"
    TemporaryStorage(store_dir)
    assert store_dir.exists()

    if os.name != "nt":
        mode = stat.S_IMODE(store_dir.stat().st_mode)
        assert mode == 0o700, f"Expected 0o700 directory permissions, got {oct(mode)}"


def test_saved_file_permissions_are_restrictive(tmp_path):
    """Architecture §6.1, AC 3: Stored files are readable/writable only by app user (0o600 on POSIX)."""
    storage = TemporaryStorage(tmp_path / "secure_store")
    path = storage.save(b"sample data", ".csv")

    assert path.exists()
    if os.name != "nt":
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"Expected 0o600 file permissions, got {oct(mode)}"


def test_storage_lifecycle_manager_initialization(tmp_path):
    storage = TemporaryStorage(tmp_path, retention_seconds=1800)
    assert isinstance(storage.lifecycle, StorageLifecycleManager)
    assert storage.retention_seconds == 1800
    assert storage.lifecycle.retention_seconds == 1800


def test_cleanup_expired_deletes_files_older_than_retention_period(tmp_path):
    """SEC-07, TC-18: Artifacts are deleted according to configured retention policy."""
    storage = TemporaryStorage(tmp_path, retention_seconds=3600)

    # File 1: Expired (2 hours old)
    file_old = storage.save(b"old dataset", ".csv")
    old_time = time.time() - 7200
    os.utime(file_old, (old_time, old_time))

    # File 2: Active / Unexpired (5 minutes old)
    file_new = storage.save(b"new dataset", ".csv")
    new_time = time.time() - 300
    os.utime(file_new, (new_time, new_time))

    deleted = storage.cleanup_expired()

    assert file_old in deleted
    assert not file_old.exists()
    assert file_new.exists()


def test_cleanup_expired_with_custom_max_age_override(tmp_path):
    """TC-18: max_age_seconds parameter explicitly overrides default retention."""
    storage = TemporaryStorage(tmp_path, retention_seconds=3600)

    f1 = storage.save(b"file 1", ".csv")
    f2 = storage.save(b"file 2", ".csv")

    # Set f1 age to 30 seconds, f2 age to 5 seconds
    now = time.time()
    os.utime(f1, (now - 30, now - 30))
    os.utime(f2, (now - 5, now - 5))

    # Cleanup with limit of 20 seconds: f1 deleted, f2 retained
    deleted = storage.cleanup_expired(max_age_seconds=20)

    assert f1 in deleted
    assert not f1.exists()
    assert f2.exists()


def test_cleanup_expired_boundary_exact_limit(tmp_path):
    """TC-18 boundary: file at limit is deleted; file younger than limit is kept."""
    storage = TemporaryStorage(tmp_path, retention_seconds=100)

    f_at_limit = storage.save(b"at limit", ".csv")
    f_under_limit = storage.save(b"under limit", ".csv")

    now = time.time()
    os.utime(f_at_limit, (now - 100, now - 100))
    os.utime(f_under_limit, (now - 99, now - 99))

    deleted = storage.cleanup_expired()

    assert f_at_limit in deleted
    assert not f_at_limit.exists()
    assert f_under_limit.exists()


def test_cleanup_expired_handles_empty_or_nonexistent_root(tmp_path):
    storage = TemporaryStorage(tmp_path / "empty_root")
    assert storage.cleanup_expired() == []


def test_cleanup_expired_never_deletes_active_paths_even_if_expired(tmp_path):
    """Active evaluation files are protected and never deleted even when exceeding retention."""
    storage = TemporaryStorage(tmp_path, retention_seconds=3600)

    active_file = storage.save(b"active model", ".joblib")
    stale_file = storage.save(b"stale model", ".joblib")

    # Age both files beyond the 3600s retention period (7200s old)
    two_hours_ago = time.time() - 7200
    os.utime(active_file, (two_hours_ago, two_hours_ago))
    os.utime(stale_file, (two_hours_ago, two_hours_ago))

    deleted = storage.cleanup_expired(active_paths=[active_file])

    assert active_file not in deleted
    assert active_file.exists()
    assert stale_file in deleted
    assert not stale_file.exists()


def test_cleanup_expired_active_paths_supports_strings_and_none(tmp_path):
    """active_paths safely handles string paths, Path objects, and None entries."""
    storage = TemporaryStorage(tmp_path, retention_seconds=100)

    f_active = storage.save(b"keep me", ".csv")
    f_stale = storage.save(b"delete me", ".csv")

    old_time = time.time() - 200
    os.utime(f_active, (old_time, old_time))
    os.utime(f_stale, (old_time, old_time))

    deleted = storage.cleanup_expired(active_paths=[str(f_active), None])

    assert f_active not in deleted
    assert f_active.exists()
    assert f_stale in deleted
    assert not f_stale.exists()


def test_cleanup_expired_active_paths_with_zero_retention_override(tmp_path):
    """Active files are protected even under extreme max_age_seconds=0 sweeps."""
    storage = TemporaryStorage(tmp_path, retention_seconds=3600)

    running_file = storage.save(b"running job", ".joblib")
    finished_file = storage.save(b"finished job", ".joblib")
    # Age both: Windows can stamp a new file a fraction of a second "in the future".
    then = time.time() - 10
    for path in (running_file, finished_file):
        os.utime(path, (then, then))

    deleted = storage.cleanup_expired(max_age_seconds=0, active_paths=[running_file])

    assert running_file not in deleted
    assert running_file.exists()
    assert finished_file in deleted
    assert not finished_file.exists()


def test_delete_evaluation_artifacts_removes_specified_files(tmp_path):
    """Explicitly clean up an evaluation's artifacts after its lifecycle ends."""
    storage = TemporaryStorage(tmp_path)
    model_path = storage.save(b"model bytes", ".joblib")
    dataset_path = storage.save(b"data bytes", ".csv")

    assert model_path.exists()
    assert dataset_path.exists()

    deleted = storage.delete_evaluation_artifacts(model_path, dataset_path)
    assert set(deleted) == {model_path, dataset_path}
    assert not model_path.exists()
    assert not dataset_path.exists()

    # Calling again with already deleted paths or None is safe and idempotent
    repeat_deleted = storage.delete_evaluation_artifacts(model_path, None)
    assert repeat_deleted == []


def test_cleanup_all_removes_all_artifacts(tmp_path):
    storage = TemporaryStorage(tmp_path)
    p1 = storage.save(b"1", ".csv")
    p2 = storage.save(b"2", ".joblib")
    assert p1.exists() and p2.exists()

    deleted = storage.lifecycle.cleanup_all()
    assert set(deleted) == {p1, p2}
    assert not p1.exists() and not p2.exists()


def test_path_traversal_filenames_never_escape_storage_root(tmp_path):
    """TC-13 / US-26: Filenames with path traversal characters cannot write outside temp directory."""
    storage = TemporaryStorage(tmp_path / "isolated_store")
    target_outside = tmp_path / "pwned.csv"

    # Verify storage saves only within root under UUID
    p = storage.save(b"safe", ".csv")
    assert p.parent.resolve() == storage.root.resolve()
    assert not target_outside.exists()


def test_api_background_retention_cleanup_e2e(tmp_path):
    """TC-18 End-to-end: API triggers background retention cleanup and deletes expired artifacts."""
    store_dir = tmp_path / "api_store"
    settings = Settings(storage_dir=store_dir, retention_seconds=60)
    app = create_app(settings)
    client = TestClient(app)

    # Seed an artificially aged file (age = 120s > 60s retention)
    old_artifact = store_dir / "old_unrelated_artifact.csv"
    old_artifact.write_bytes(b"col1,col2\n1,2\n")
    old_time = time.time() - 120
    os.utime(old_artifact, (old_time, old_time))
    assert old_artifact.exists()

    model_file, data_file = write_classification_fixture(tmp_path)
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": (model_file.name, model_file.read_bytes()),
            "dataset": (data_file.name, data_file.read_bytes()),
        },
    )
    assert response.status_code == 202

    # The background task executes cleanup_expired; old artifact should be deleted
    assert not old_artifact.exists()

    # The newly uploaded evaluation artifacts must remain present
    stored_now = list(store_dir.glob("*.joblib")) + list(store_dir.glob("*.csv"))
    assert len(stored_now) == 2
    assert all(p.exists() for p in stored_now)
