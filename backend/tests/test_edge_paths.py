"""Unit tests for edge paths that were not exercised: a failed partial write, a framework 5xx error,
the authentication middleware's settings lookup and non-request events, and validation without files."""

import io

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.auth import AuthenticationMiddleware
from app.api.error_handlers import register_error_handlers
from app.config import Settings
from app.main import create_app
from app.storage import TemporaryStorage
from app.validation.service import validate_submission

# --- storage: a write that fails halfway ---------------------------------------------------------------


class FailingStream(io.RawIOBase):
    """Yields some bytes, then fails like a full disk or a dropped connection would."""

    def __init__(self):
        self.reads = 0

    def readable(self):
        return True

    def read(self, size=-1):
        self.reads += 1
        if self.reads > 1:
            raise OSError("connection reset")
        return b"some bytes"


def test_a_failed_partial_write_leaves_no_file_behind(tmp_path):
    storage = TemporaryStorage(tmp_path / "store")

    with pytest.raises(OSError, match="connection reset"):
        storage.save(FailingStream(), ".csv")

    assert list(storage.root.iterdir()) == []


# --- error handling: a 5xx raised by the framework -------------------------------------------------------


def test_a_framework_server_error_is_reported_generically():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    def boom():
        raise HTTPException(status_code=503, detail="database down at /srv/private/db.sqlite")

    response = TestClient(app).get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "database" not in response.text and "/srv" not in response.text


# --- authentication middleware -----------------------------------------------------------------------------


def app_with_protected_route(**middleware_options):
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware, **middleware_options)

    @app.get("/api/evaluations/x")
    def protected():
        return {"ok": True}

    return app


def test_the_middleware_uses_settings_given_to_it_directly():
    app = app_with_protected_route(settings=Settings(auth_enabled=True, api_key="the-key"))
    client = TestClient(app)

    assert client.get("/api/evaluations/x").status_code == 401
    assert client.get("/api/evaluations/x", headers={"X-API-Key": "the-key"}).status_code == 200


def test_without_any_settings_the_middleware_falls_back_to_the_environment(monkeypatch):
    monkeypatch.setenv("MLEVAL_AUTH_ENABLED", "true")
    monkeypatch.setenv("MLEVAL_API_KEY", "from-the-environment")
    client = TestClient(app_with_protected_route())  # no settings on the app, none passed in

    assert client.get("/api/evaluations/x").status_code == 401
    assert client.get("/api/evaluations/x", headers={"X-API-Key": "from-the-environment"}).status_code == 200


def test_events_that_are_not_http_requests_pass_through_untouched(settings):
    """Starting and stopping the application (lifespan events) must not be treated as a request."""
    with TestClient(create_app(settings)) as client:  # entering the block runs startup and shutdown
        assert client.get("/api/health").status_code == 200


# --- validation without file contents -----------------------------------------------------------------------


def test_validation_of_names_and_settings_alone_needs_no_files():
    validate_submission(
        model_filename="model.joblib",
        dataset_filename="data.csv",
        task_type="classification",
        target_column="label",
        settings=Settings(),
    )  # raises nothing: only the file contents are checked when the files are given


def test_an_authorization_header_that_is_not_bearer_is_not_accepted_as_a_key():
    app = app_with_protected_route(settings=Settings(auth_enabled=True, api_key="the-key"))
    client = TestClient(app)

    response = client.get("/api/evaluations/x", headers={"Authorization": "Basic the-key"})

    assert response.status_code == 401
