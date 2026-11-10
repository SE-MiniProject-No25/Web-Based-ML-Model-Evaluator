"""API Error Handler: turns exceptions into the safe error format (Architecture sections 10.4 and 11)."""

import logging
import re
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

GENERIC_500_MESSAGE = "An unexpected error occurred."

_SAFE_HTTP_MESSAGES = {
    400: "Bad request.",
    401: "Authentication required.",
    403: "Access forbidden.",
    404: "The requested resource was not found.",
    405: "Method not allowed.",
    413: "The request file exceeds the maximum allowed size.",
    415: "The file format is not supported.",
    422: "The request content is unprocessable.",
    500: GENERIC_500_MESSAGE,
}

_CONTROLLED_DOMAIN_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.MISSING_REQUIRED_FIELD: "One or more required fields are missing.",
    ErrorCode.UNAUTHENTICATED: "Authentication required.",
    ErrorCode.UNSUPPORTED_FILE_TYPE: "The uploaded file type is not supported.",
    ErrorCode.FILE_TOO_LARGE: "The uploaded file exceeds the maximum allowed size.",
    ErrorCode.MALFORMED_DATASET: "The dataset file is malformed or invalid.",
    ErrorCode.INVALID_MODEL: "The model file could not be loaded or is invalid.",
    ErrorCode.INVALID_TARGET_COLUMN: "The selected target column does not exist in the dataset.",
    ErrorCode.INVALID_TASK_TYPE: "The specified task type is not supported.",
    ErrorCode.EVALUATION_NOT_FOUND: "Evaluation not found.",
    ErrorCode.EVALUATION_NOT_COMPLETED: "Evaluation not completed.",
    ErrorCode.INCOMPATIBLE_INPUTS: "The model and dataset are incompatible.",
    ErrorCode.RESOURCE_LIMIT_EXCEEDED: "The evaluation exceeded resource limits.",
    ErrorCode.EVALUATION_FAILED: "The evaluation failed.",
}

_TRUSTED_STATIC_DOMAIN_MESSAGES: dict[ErrorCode, set[str]] = {
    ErrorCode.MALFORMED_DATASET: {
        "The dataset file is empty.",
        "The dataset file could not be parsed as UTF-8 text.",
        "The dataset file contains null bytes.",
        "The dataset file is malformed.",
        "The dataset file is missing a header row.",
        "The dataset file contains ragged rows with inconsistent column counts.",
    },
    ErrorCode.INVALID_MODEL: {
        "The model file could not be loaded or is corrupted.",
        "The model file must have a callable predict method.",
    },
    ErrorCode.INVALID_TASK_TYPE: {
        "The task type must be one of: classification, regression.",
    },
    ErrorCode.EVALUATION_NOT_FOUND: {
        "Evaluation not found.",
    },
    ErrorCode.EVALUATION_NOT_COMPLETED: {
        "Evaluation not completed.",
    },
    ErrorCode.UNAUTHENTICATED: {
        "Authentication required.",
    },
    ErrorCode.INVALID_TARGET_COLUMN: {
        "The selected target column does not exist.",
    },
}

_TRUSTED_DYNAMIC_PATTERNS: dict[ErrorCode, re.Pattern[str]] = {
    ErrorCode.MISSING_REQUIRED_FIELD: re.compile(
        r"^Missing required field\(s\): (?:model|dataset|task_type|target_column)"
        r"(?:, (?:model|dataset|task_type|target_column))*\.$"
    ),
    ErrorCode.UNSUPPORTED_FILE_TYPE: re.compile(
        r"^The (?:model|dataset) must be one of: \.[a-zA-Z0-9]+(?:, \.[a-zA-Z0-9]+)*\.$"
    ),
    ErrorCode.FILE_TOO_LARGE: re.compile(
        r"^The (?:model|dataset) file exceeds the (?:maximum allowed size|limit) of \d+ bytes\.$"
    ),
    ErrorCode.INVALID_TARGET_COLUMN: re.compile(
        r"^The selected target column '[a-zA-Z0-9_.-]{1,64}' does not exist in the dataset\.$"
    ),
}

_ALLOWED_FIELD_NAMES = {
    "model",
    "dataset",
    "task_type",
    "target_column",
    "evaluation_id",
    # test payload fields
    "count",
    "tag",
    "code",
}


def _is_trusted_domain_message(code: ErrorCode, message: str) -> bool:
    """Validate whether an AppError message matches an authorized, controlled domain template."""
    if message in _TRUSTED_STATIC_DOMAIN_MESSAGES.get(code, set()):
        return True
    pattern = _TRUSTED_DYNAMIC_PATTERNS.get(code)
    if pattern and pattern.match(message):
        return True
    return False


def _format_error_response(code: str, message: str, status_code: int) -> JSONResponse:
    """Return a consistent {"error": {"code": ..., "message": ...}} JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    """Handle domain AppError exceptions with their defined HTTP status (Architecture section 11).

    If an AppError has no HTTP status (e.g. post-202 runner errors like INCOMPATIBLE_INPUTS),
    do not expose it to an HTTP caller; return the generic 500 response and log details server-side.
    Domain error responses use controlled public messages associated with their error codes.
    """
    if exc.status_code is None:
        logger.error("AppError without HTTP status raised in API context: %s", exc.code)
        return _format_error_response("INTERNAL_SERVER_ERROR", GENERIC_500_MESSAGE, 500)

    if _is_trusted_domain_message(exc.code, exc.message):
        message = exc.message
    else:
        logger.warning(
            "AppError for code %s used unrecognized message; using controlled public message",
            exc.code,
        )
        message = _CONTROLLED_DOMAIN_MESSAGES.get(exc.code, "Validation failed.")

    return _format_error_response(exc.code.value, message, exc.status_code)


def _status_to_code(status_code: int) -> str:
    """Map common HTTP status codes to standard error code names."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        413: "FILE_TOO_LARGE",
        415: "UNSUPPORTED_FILE_TYPE",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


async def _handle_http_exception(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette and FastAPI HTTPExceptions with the consistent error envelope.

    Framework exceptions strictly use predefined safe public messages to prevent exposing internal details.
    """
    code = _status_to_code(exc.status_code)
    message = _SAFE_HTTP_MESSAGES.get(exc.status_code, "An error occurred.")

    if exc.status_code >= 500:
        logger.error("Server HTTPException (%d) occurred", exc.status_code)
        return _format_error_response("INTERNAL_SERVER_ERROR", GENERIC_500_MESSAGE, 500)

    logger.warning("HTTPException (%d: %s) handled with safe public message", exc.status_code, code)
    return _format_error_response(code, message, exc.status_code)


async def _handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors without leaking schemas, raw inputs, or arbitrary locations."""
    summary = []
    for err in exc.errors():
        loc_parts = [str(p) for p in err.get("loc", []) if p != "body"]
        raw_loc = ".".join(loc_parts)
        safe_loc = raw_loc if raw_loc in _ALLOWED_FIELD_NAMES else "<unknown-field>"
        summary.append({
            "loc": safe_loc,
            "type": str(err.get("type", "")),
        })
    logger.warning("Request validation failed: %s", summary)

    error_messages = []
    has_missing = False

    for error in exc.errors():
        loc_parts = [str(p) for p in error.get("loc", []) if p != "body"]
        raw_loc = ".".join(loc_parts)
        is_known = raw_loc in _ALLOWED_FIELD_NAMES
        err_type = str(error.get("type", ""))

        if "missing" in err_type:
            has_missing = True
            msg = f"Field '{raw_loc}' is required." if is_known else "Required field is missing."
        else:
            msg = f"Field '{raw_loc}' has an invalid value." if is_known else "Invalid field provided."

        error_messages.append(msg)

    safe_message = "; ".join(error_messages) if error_messages else "Request validation failed."
    code = "MISSING_REQUIRED_FIELD" if has_missing else "VALIDATION_ERROR"
    return _format_error_response(code, safe_message, 422)


async def _handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions (NFR-05, SEC-05).

    Logs diagnostic stack frames (file, function, line) and the matched route template.
    Does not log raw request paths, query parameters, or raw exception messages.
    No traceback, filesystem path, or internal configuration reaches the client.
    """
    tb_frames = [
        f'  File "{f.filename}", line {f.lineno}, in {f.name}'
        for f in traceback.extract_tb(exc.__traceback__)
    ]
    tb_summary = "\n".join(tb_frames) if tb_frames else "  No stack frames available."

    route = request.scope.get("route")
    route_path = getattr(route, "path", None) or "<unknown-route>"

    logger.error(
        "Unhandled server exception (%s) processing %s %s:\n%s",
        type(exc).__name__,
        request.method,
        route_path,
        tb_summary,
    )
    return _format_error_response("INTERNAL_SERVER_ERROR", GENERIC_500_MESSAGE, 500)


def register_error_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""
    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_exception)
