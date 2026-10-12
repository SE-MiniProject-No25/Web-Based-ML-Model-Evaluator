import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.error_handlers import register_error_handlers
from app.errors import HTTP_STATUS, AppError, ErrorCode


def test_every_error_code_has_a_status_entry():
    assert set(HTTP_STATUS) == set(ErrorCode)


@pytest.mark.parametrize(
    ("code", "status"),
    [
        (ErrorCode.MISSING_REQUIRED_FIELD, 400),
        (ErrorCode.UNSUPPORTED_FILE_TYPE, 415),
        (ErrorCode.FILE_TOO_LARGE, 413),
        (ErrorCode.INVALID_TARGET_COLUMN, 422),
        (ErrorCode.EVALUATION_NOT_FOUND, 404),
        (ErrorCode.EVALUATION_NOT_COMPLETED, 409),
        (ErrorCode.EVALUATION_FAILED, None),
    ],
)
def test_status_codes_match_architecture_table(code, status):
    assert AppError(code, "x").status_code == status


def test_error_body_has_code_and_message_only():
    err = AppError(ErrorCode.INVALID_TARGET_COLUMN, "The selected target column does not exist.")
    assert err.to_response_body() == {
        "error": {
            "code": "INVALID_TARGET_COLUMN",
            "message": "The selected target column does not exist.",
        }
    }


def test_api_returns_app_error_in_the_standard_format():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    def boom():
        raise AppError(ErrorCode.EVALUATION_NOT_FOUND, "Evaluation not found.")

    response = TestClient(app).get("/boom")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "EVALUATION_NOT_FOUND", "message": "Evaluation not found."}}
