from app.config import Settings, load_settings


def test_defaults_cover_every_required_setting():
    s = Settings()
    assert ".joblib" in s.allowed_model_extensions and ".csv" in s.allowed_dataset_extensions
    assert s.max_upload_bytes > 0
    assert s.evaluation_timeout_seconds > 0
    assert s.retention_seconds > 0
    assert s.auth_enabled is False


def test_environment_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("MLEVAL_MAX_UPLOAD_BYTES", "1234")
    monkeypatch.setenv("MLEVAL_AUTH_ENABLED", "true")
    monkeypatch.setenv("MLEVAL_STORAGE_DIR", str(tmp_path))
    s = load_settings()
    assert s.max_upload_bytes == 1234
    assert s.auth_enabled is True
    assert s.storage_dir == tmp_path
