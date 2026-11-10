import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, field_validator

from app.api.error_handlers import _CONTROLLED_DOMAIN_MESSAGES, register_error_handlers
from app.config import Settings
from app.errors import HTTP_STATUS, AppError, ErrorCode
from app.main import create_app
from tests.helpers import write_classification_fixture, write_regression_fixture


def test_every_error_code_has_a_status_entry():
    assert set(ErrorCode) == set(HTTP_STATUS)


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (ErrorCode.MISSING_REQUIRED_FIELD, 400),
        (ErrorCode.UNAUTHENTICATED, 401),
        (ErrorCode.UNSUPPORTED_FILE_TYPE, 415),
        (ErrorCode.FILE_TOO_LARGE, 413),
        (ErrorCode.MALFORMED_DATASET, 422),
        (ErrorCode.INVALID_MODEL, 422),
        (ErrorCode.INVALID_TARGET_COLUMN, 422),
        (ErrorCode.INVALID_TASK_TYPE, 422),
        (ErrorCode.INCOMPATIBLE_INPUTS, None),
        (ErrorCode.RESOURCE_LIMIT_EXCEEDED, None),
        (ErrorCode.EVALUATION_FAILED, None),
        (ErrorCode.EVALUATION_NOT_FOUND, 404),
        (ErrorCode.EVALUATION_NOT_COMPLETED, 409),
    ],
)
def test_status_codes_match_architecture_table(code, status):
    assert HTTP_STATUS[code] == status


def test_error_body_has_code_and_message_only():
    err = AppError(ErrorCode.INVALID_TARGET_COLUMN, "The selected target column does not exist.")
    body = err.to_response_body()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body == {
        "error": {
            "code": "INVALID_TARGET_COLUMN",
            "message": "The selected target column does not exist.",
        }
    }


@pytest.mark.parametrize(
    "code",
    [code for code, status in HTTP_STATUS.items() if status is not None],
)
def test_every_http_error_code_returns_standard_response(code):
    app = FastAPI()
    register_error_handlers(app)
    expected_status = HTTP_STATUS[code]

    @app.get("/trigger")
    def trigger():
        raise AppError(code, f"Sample error for {code.value}")

    client = TestClient(app)
    response = client.get("/trigger")
    assert response.status_code == expected_status
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == code.value
    assert body["error"]["message"] == _CONTROLLED_DOMAIN_MESSAGES[code]


def test_app_error_without_http_status_returns_generic_500_without_leaking_details(caplog):
    """If an AppError with no HTTP status is raised in the API, return generic 500 and log server-side."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/unmapped-app-error")
    def unmapped():
        raise AppError(
            ErrorCode.EVALUATION_FAILED,
            "Internal runner failed at /var/secrets/key.pem with token=hunter2",
        )

    with caplog.at_level(logging.ERROR):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/unmapped-app-error")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred.",
    }
    # Response contains no paths, secrets, or tracebacks
    assert "hunter2" not in response.text
    assert "/var/secrets" not in response.text
    assert "Traceback" not in response.text

    # Diagnostic details are preserved server-side in logs without leaking credentials
    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "AppError without HTTP status" in logged
    assert "hunter2" not in logged


def test_app_error_with_unrecognized_secret_message_uses_controlled_message(caplog):
    """AppError with an unrecognized secret-like message uses the controlled public message."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/secret-app-error")
    def secret_domain_error():
        raise AppError(
            ErrorCode.INVALID_MODEL,
            "unrecognized-secret-database-token-xyz-98765",
        )

    with caplog.at_level(logging.WARNING):
        client = TestClient(app)
        response = client.get("/secret-app-error")

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "INVALID_MODEL"
    assert body["error"]["message"] == "The model file could not be loaded or is invalid."
    assert "unrecognized-secret-database-token-xyz-98765" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "unrecognized-secret-database-token-xyz-98765" not in logged
    assert "unrecognized message" in logged


def test_http_exception_with_unrecognized_secret_detail_never_reaches_client():
    """HTTPException with a short secret-like string never reaches the client (Directive 1)."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/secret-http-exc")
    def secret_exc():
        raise HTTPException(status_code=400, detail="my-private-database-password")

    client = TestClient(app)
    response = client.get("/secret-http-exc")

    assert response.status_code == 400
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "BAD_REQUEST"
    assert body["error"]["message"] == "Bad request."
    assert "my-private-database-password" not in response.text


def test_http_exception_with_dictionary_detail_is_sanitized(caplog):
    """HTTPException with a dictionary detail does not pass arbitrary dictionaries to the client."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/dict-http-exc")
    def dict_exc():
        raise HTTPException(
            status_code=403,
            detail={"internal_token": "secret_abc123", "server_path": "C:\\srv\\conf"},
        )

    with caplog.at_level(logging.WARNING):
        client = TestClient(app)
        response = client.get("/dict-http-exc")

    assert response.status_code == 403
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"] == {
        "code": "FORBIDDEN",
        "message": "Access forbidden.",
    }
    assert "secret_abc123" not in response.text
    assert "C:\\srv" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "safe public message" in logged
    assert "secret_abc123" not in logged


def test_validation_error_with_arbitrary_secret_does_not_appear_in_logs_or_response(caplog):
    """Arbitrary secret-like validator message does not appear in logs or response (Directive 4)."""
    app = FastAPI()
    register_error_handlers(app)

    class SecretPayload(BaseModel):
        code: str

        @field_validator("code")
        @classmethod
        def validate_code(cls, v: str) -> str:
            if v != "valid":
                raise ValueError("arbitrary-secret-val-custom-validator-xyz999")
            return v

    @app.post("/test-secret-val")
    def secret_endpoint(payload: SecretPayload):
        return {"ok": True}

    with caplog.at_level(logging.WARNING):
        client = TestClient(app)
        response = client.post("/test-secret-val", json={"code": "invalid_input"})

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Field 'code' has an invalid value."
    assert "arbitrary-secret-val-custom-validator-xyz999" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert "arbitrary-secret-val-custom-validator-xyz999" not in logged
    assert "Request validation failed" in logged
    assert "'loc': 'code'" in logged
    assert "'type': 'value_error'" in logged


def test_unexpected_exception_returns_500_without_leaking_details(caplog):
    """NFR-05, SEC-05: Unhandled exceptions return generic 500 without stack trace, paths, or secrets."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/crash")
    def crash():
        raise RuntimeError("Database connection at /var/secrets/db.key failed: password=hunter2")

    with caplog.at_level(logging.ERROR):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/crash")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
        }
    }
    # Client never sees internal details, secrets, paths, or tracebacks
    assert "hunter2" not in response.text
    assert "/var/secrets" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text


def test_unexpected_exception_redacts_credentials_in_server_logs(caplog):
    """Unexpected exceptions omit raw messages from server logs while preserving diagnostics."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/crash-with-secrets")
    def crash():
        raise RuntimeError(
            "Connection failed: password=supersecretpassword123 and token=ghp_secrettoken99999"
        )

    with caplog.at_level(logging.ERROR):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/crash-with-secrets")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "supersecretpassword123" not in response.text
    assert "ghp_secrettoken99999" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    # Raw exception message credentials must never appear in server logs
    assert "supersecretpassword123" not in logged
    assert "ghp_secrettoken99999" not in logged

    # Diagnostic context must be preserved
    assert "Unhandled server exception (RuntimeError)" in logged
    assert "crash-with-secrets" in logged
    assert "test_errors.py" in logged
    assert "in crash" in logged


def test_unexpected_exception_with_arbitrary_secret_format_never_logged_or_exposed(caplog):
    """Unhandled exception with arbitrary secret format (no keywords) is never logged or exposed."""
    app = FastAPI()
    register_error_handlers(app)

    arbitrary_secret = "XYZZY_987654321_OPAQUE_PRIVATE_CREDENTIAL"

    @app.get("/unhandled-arbitrary-secret")
    def crash():
        raise RuntimeError(f"Database driver failed: {arbitrary_secret}")

    with caplog.at_level(logging.ERROR):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/unhandled-arbitrary-secret?api_key=query_secret_to_ignore")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred.",
    }
    # Response never contains secret or query params
    assert arbitrary_secret not in response.text
    assert "query_secret_to_ignore" not in response.text
    assert "RuntimeError" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    # Server logs never contain arbitrary secret or sensitive query parameters
    assert arbitrary_secret not in logged
    assert "query_secret_to_ignore" not in logged

    # Stack-frame diagnostics remain available
    assert "Unhandled server exception (RuntimeError)" in logged
    assert "unhandled-arbitrary-secret" in logged
    assert "test_errors.py" in logged
    assert "in crash" in logged


def test_unexpected_exception_with_sensitive_path_value_never_logged_or_exposed(caplog):
    """An unexpected exception with a sensitive value in its path is not exposed in logs or response."""
    app = FastAPI()
    register_error_handlers(app)

    sensitive_path_token = "SECRET_PATH_TOKEN_12345"

    @app.get("/items/{item_id}")
    def crash_item(item_id: str):
        raise RuntimeError("Crash occurred during item processing.")

    with caplog.at_level(logging.ERROR):
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get(f"/items/{sensitive_path_token}?query_secret=DO_NOT_LOG")

    assert response.status_code == 500
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"] == {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred.",
    }
    assert sensitive_path_token not in response.text
    assert "query_secret" not in response.text
    assert "DO_NOT_LOG" not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    # Sensitive path value and query parameters are never logged
    assert sensitive_path_token not in logged
    assert "query_secret" not in logged
    assert "DO_NOT_LOG" not in logged

    # Route template and diagnostic frames are logged
    assert "/items/{item_id}" in logged
    assert "Unhandled server exception (RuntimeError)" in logged
    assert "test_errors.py" in logged
    assert "in crash_item" in logged


def test_validation_error_with_attacker_controlled_location_is_not_exposed(caplog):
    """A validation error with an attacker-controlled location does not expose it in logs or response."""
    app = FastAPI()
    register_error_handlers(app)

    class ForbidExtraModel(BaseModel):
        model_config = ConfigDict(extra="forbid")
        tag: str

    @app.post("/forbid-extra")
    def forbid_endpoint(payload: ForbidExtraModel):
        return {"ok": True}

    attacker_loc = "ATTACKER_CONTROLLED_SECRET_KEY_77777"

    with caplog.at_level(logging.WARNING):
        client = TestClient(app)
        response = client.post("/forbid-extra", json={"tag": "valid", attacker_loc: "extra_val"})

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Invalid field provided."
    assert attacker_loc not in response.text

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert attacker_loc not in logged
    assert "Request validation failed" in logged
    assert "<unknown-field>" in logged


def test_framework_http_exceptions_use_standard_error_format():
    """Starlette/FastAPI HTTPExceptions (e.g. 404, 405) adhere to the standard envelope."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/valid")
    def valid():
        return {"status": "ok"}

    @app.get("/custom-403")
    def custom_403():
        raise HTTPException(status_code=403, detail="Access denied to resource.")

    client = TestClient(app)

    # 404 Not Found
    r_404 = client.get("/no-such-endpoint")
    assert r_404.status_code == 404
    body_404 = r_404.json()
    assert set(body_404) == {"error"}
    assert set(body_404["error"]) == {"code", "message"}
    assert body_404["error"]["code"] == "NOT_FOUND"

    # 405 Method Not Allowed
    r_405 = client.post("/valid")
    assert r_405.status_code == 405
    body_405 = r_405.json()
    assert set(body_405) == {"error"}
    assert set(body_405["error"]) == {"code", "message"}
    assert body_405["error"]["code"] == "METHOD_NOT_ALLOWED"

    # Custom HTTPException
    r_403 = client.get("/custom-403")
    assert r_403.status_code == 403
    body_403 = r_403.json()
    assert set(body_403) == {"error"}
    assert set(body_403["error"]) == {"code", "message"}
    assert body_403["error"]["code"] == "FORBIDDEN"
    assert body_403["error"]["message"] == "Access forbidden."


def test_request_validation_missing_and_invalid_types():
    """Pydantic validation errors adhere to {"error": {"code", "message"}}."""
    app = FastAPI()
    register_error_handlers(app)

    class Payload(BaseModel):
        count: int
        tag: str

    @app.post("/test-validation")
    def test_val(payload: Payload):
        return {"ok": True}

    client = TestClient(app)

    # Missing field
    r_missing = client.post("/test-validation", json={"count": 10})
    assert r_missing.status_code == 422
    body = r_missing.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "MISSING_REQUIRED_FIELD"
    assert "tag" in body["error"]["message"]

    # Invalid type
    r_invalid = client.post("/test-validation", json={"count": "not-an-int", "tag": "test"})
    assert r_invalid.status_code == 422
    body = r_invalid.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "count" in body["error"]["message"]


# =================================================================================================
# TC-16: End-to-end security verification against information disclosure
# =================================================================================================


def test_tc16_server_validation_error_leaks_no_trace_or_path(tmp_path):
    """TC-16 (validation half): server-side validation failure response has no raw trace or paths."""
    client = TestClient(create_app(Settings(storage_dir=tmp_path / "uploads")))
    model, _ = write_classification_fixture(tmp_path)

    # Malformed CSV (ragged rows)
    ragged_csv = b"a,b,label\n1.0,2.0,1\n3.0\n"
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model.read_bytes()),
            "dataset": ("ragged.csv", ragged_csv),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message"}
    assert body["error"]["code"] == "MALFORMED_DATASET"

    # Security assertions: no internal trace, paths, or secrets leaked
    assert "Traceback" not in response.text
    assert str(tmp_path) not in response.text
    assert "backend" not in response.text
    assert "app." not in response.text


def test_tc16_runtime_evaluation_error_leaks_no_trace_or_path(tmp_path):
    """TC-16 (evaluation half): runtime evaluation failure response has no raw trace or paths."""
    client = TestClient(create_app(Settings(storage_dir=tmp_path / "uploads")))
    model, _ = write_classification_fixture(tmp_path / "c")
    _, mismatched_data = write_regression_fixture(tmp_path / "r", target="label")

    # Submit incompatible model/dataset
    submit_resp = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model.read_bytes()),
            "dataset": ("data.csv", mismatched_data.read_bytes()),
        },
    )
    assert submit_resp.status_code == 202
    eval_id = submit_resp.json()["evaluation_id"]

    # Query status endpoint for the failed evaluation
    status_resp = client.get(f"/api/evaluations/{eval_id}")
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] == "failed"
    assert "error" in body
    assert set(body["error"]) == {"code", "message"}
    assert "metrics" not in body

    # Security assertions: no raw trace, paths, or secrets
    assert "Traceback" not in status_resp.text
    assert str(tmp_path) not in status_resp.text
    assert "backend" not in status_resp.text
    assert "app." not in status_resp.text
