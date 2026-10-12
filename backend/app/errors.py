"""Shared error type and error format (Architecture section 10.4 and 11).

Every component raises ``AppError``; the API layer turns it into the
``{"error": {"code", "message"}}`` response. This module sits below all
components so that validation, evaluation and results can use it without
importing from ``api``.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Error codes from the Architecture section 11 table."""

    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    MALFORMED_DATASET = "MALFORMED_DATASET"
    INVALID_MODEL = "INVALID_MODEL"
    INVALID_TARGET_COLUMN = "INVALID_TARGET_COLUMN"
    INVALID_TASK_TYPE = "INVALID_TASK_TYPE"
    INCOMPATIBLE_INPUTS = "INCOMPATIBLE_INPUTS"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    EVALUATION_FAILED = "EVALUATION_FAILED"
    EVALUATION_NOT_FOUND = "EVALUATION_NOT_FOUND"
    EVALUATION_NOT_COMPLETED = "EVALUATION_NOT_COMPLETED"


# HTTP status per code. Codes mapped to None only occur after the request was
# accepted with 202, so they are stored on the evaluation and never returned
# as an HTTP error (Architecture section 11).
HTTP_STATUS = {
    ErrorCode.MISSING_REQUIRED_FIELD: 400,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.UNSUPPORTED_FILE_TYPE: 415,
    ErrorCode.FILE_TOO_LARGE: 413,
    ErrorCode.MALFORMED_DATASET: 422,
    ErrorCode.INVALID_MODEL: 422,
    ErrorCode.INVALID_TARGET_COLUMN: 422,
    ErrorCode.INVALID_TASK_TYPE: 422,
    ErrorCode.INCOMPATIBLE_INPUTS: None,
    ErrorCode.RESOURCE_LIMIT_EXCEEDED: None,
    ErrorCode.EVALUATION_FAILED: None,
    ErrorCode.EVALUATION_NOT_FOUND: 404,
    ErrorCode.EVALUATION_NOT_COMPLETED: 409,
}


class AppError(Exception):
    """An error that is safe to show to the client.

    ``message`` must never contain stack traces, filesystem paths or other
    internal details (SEC-05).
    """

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    @property
    def status_code(self):
        """HTTP status for this error, or None for post-202 evaluation errors."""
        return HTTP_STATUS[self.code]

    def to_dict(self) -> dict:
        """The error object: ``{"code": ..., "message": ...}``."""
        return {"code": self.code.value, "message": self.message}

    def to_response_body(self) -> dict:
        """The full API error body: ``{"error": {"code", "message"}}``."""
        return {"error": self.to_dict()}
