"""Unit tests for edge cases in small components: the storage lifecycle, the metrics service, the
child-process environment and the settings."""

import logging
import os
import sys
import time

import pytest

from app.config import Settings
from app.metrics import service as metrics_service
from app.security import sanitized_env
from app.storage import TemporaryStorage

# --- storage lifecycle ------------------------------------------------------------------------------


@pytest.fixture
def storage(tmp_path):
    return TemporaryStorage(tmp_path / "store", retention_seconds=3600)


def age(path, seconds):
    then = time.time() - seconds
    os.utime(path, (then, then))


def test_a_negative_age_limit_is_treated_as_zero(storage):
    path = storage.save(b"x", ".csv")
    age(path, 1)
    assert storage.cleanup_expired(max_age_seconds=-50) == [path]


def test_directories_inside_the_store_are_never_deleted_by_the_sweep(storage):
    folder = storage.root / "subfolder"
    folder.mkdir()
    age(folder, 99999)

    assert storage.cleanup_expired(max_age_seconds=0) == []
    assert folder.exists()


def test_a_file_that_cannot_be_deleted_is_logged_and_does_not_stop_the_sweep(storage, monkeypatch, caplog):
    first, second = storage.save(b"1", ".csv"), storage.save(b"2", ".csv")
    # Windows can stamp a new file a fraction of a second "in the future", so age them clearly.
    age(first, 10)
    age(second, 10)
    real_delete = storage.delete

    def delete_unless_first(path):
        if path.name == first.name:
            raise PermissionError("in use")
        real_delete(path)

    monkeypatch.setattr(storage, "delete", delete_unless_first)

    with caplog.at_level(logging.WARNING):
        deleted = storage.cleanup_expired(max_age_seconds=0)

    assert deleted == [second]
    assert first.exists() and not second.exists()
    assert "Failed to inspect or delete" in caplog.text


def test_deleting_evaluation_artifacts_skips_missing_files_and_logs_failures(storage, monkeypatch, caplog):
    present = storage.save(b"x", ".csv")
    outside = storage.root.parent / "elsewhere.txt"
    outside.write_text("keep")

    with caplog.at_level(logging.WARNING):
        deleted = storage.delete_evaluation_artifacts(present, None, storage.root / "missing.csv", outside)

    assert deleted == [present]
    assert outside.exists()  # a file outside the store is refused, not deleted
    assert "Failed to delete evaluation artifact" in caplog.text


def test_cleanup_all_removes_files_but_not_folders(storage):
    one, two = storage.save(b"1", ".csv"), storage.save(b"2", ".joblib")
    folder = storage.root / "keep"
    folder.mkdir()

    assert sorted(storage.lifecycle.cleanup_all()) == sorted([one, two])
    assert folder.exists() and not one.exists() and not two.exists()


def test_cleanup_all_logs_and_continues_when_a_delete_fails(storage, monkeypatch, caplog):
    storage.save(b"1", ".csv")
    monkeypatch.setattr(storage, "delete", lambda path: (_ for _ in ()).throw(PermissionError("in use")))

    with caplog.at_level(logging.WARNING):
        assert storage.lifecycle.cleanup_all() == []

    assert "Failed to delete" in caplog.text


def test_sweeping_a_store_whose_folder_disappeared_is_harmless(storage):
    storage.root.rmdir()
    assert storage.cleanup_expired() == []
    assert storage.lifecycle.cleanup_all() == []


# --- metrics --------------------------------------------------------------------------------------


def test_a_non_finite_r2_is_reported_as_zero_so_the_result_stays_valid(monkeypatch):
    monkeypatch.setattr(metrics_service, "r2_score", lambda *args, **kwargs: float("nan"))

    metrics = metrics_service.compute("regression", [1.0, 2.0, 3.0], [1.0, 2.0, 3.0])

    assert metrics["r2"] == 0.0
    assert metrics["mae"] == 0.0


# --- the child-process environment --------------------------------------------------------------------


def test_the_child_environment_has_no_server_secrets(monkeypatch):
    monkeypatch.setenv("MLEVAL_API_KEY", "super-secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "also-secret")

    env = sanitized_env()

    assert "super-secret" not in env.values() and "also-secret" not in env.values()
    assert set(env) <= {
        "SYSTEMROOT", "PATH", "PYTHONHASHSEED", "PYTHONPATH", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "TEMP", "TMP", "WINDIR", "USERPROFILE",
    }  # fmt: skip


def test_the_child_gets_the_servers_import_paths_and_one_thread_per_library():
    env = sanitized_env()
    assert env["PYTHONPATH"] == os.pathsep.join(p for p in sys.path if p)
    assert (env["OMP_NUM_THREADS"], env["OPENBLAS_NUM_THREADS"], env["MKL_NUM_THREADS"]) == ("1", "1", "1")


def test_optional_windows_variables_are_only_passed_when_they_exist(monkeypatch):
    for name in ("TEMP", "TMP", "WINDIR", "USERPROFILE"):
        monkeypatch.delenv(name, raising=False)
    assert not {"TEMP", "TMP", "WINDIR", "USERPROFILE"} & set(sanitized_env())

    monkeypatch.setenv("TEMP", "C:/tmp")
    assert sanitized_env()["TEMP"] == "C:/tmp"


# --- settings ---------------------------------------------------------------------------------------


def test_all_allowed_extensions_combine_models_and_datasets():
    extensions = Settings().allowed_extensions
    assert {".joblib", ".pkl", ".csv"} <= set(extensions)
