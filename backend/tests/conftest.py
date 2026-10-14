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
