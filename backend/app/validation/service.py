"""Input Validation Service.

MINIMAL VERSION so POST /api/evaluations is safe on its own: it checks that every
field is present, that both files have an allowed extension and that the task
type is supported. US-06 (size limits), US-07 (malformed CSV / model files) and
US-08 (task type and target column against the dataset) extend this module;
keep ``validate_submission`` as the single entry point the API calls.
"""

from pathlib import PurePosixPath

from app.config import Settings
from app.errors import AppError, ErrorCode

TASK_TYPES = ("classification", "regression")


def _extension(filename: str) -> str:
    return PurePosixPath(filename.replace("\\", "/")).suffix.lower()


def validate_submission(
    *,
    model_filename: str | None,
    dataset_filename: str | None,
    task_type: str | None,
    target_column: str | None,
    settings: Settings,
) -> None:
    """Raise an ``AppError`` (Architecture section 11) if the submission must be rejected."""
    missing = [
        name
        for name, value in (
            ("model", model_filename),
            ("dataset", dataset_filename),
            ("task_type", task_type),
            ("target_column", target_column),
        )
        if not value or not value.strip()
    ]
    if missing:
        raise AppError(ErrorCode.MISSING_REQUIRED_FIELD, f"Missing required field(s): {', '.join(missing)}.")

    if _extension(model_filename) not in settings.allowed_model_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The model must be one of: {', '.join(settings.allowed_model_extensions)}.",
        )
    if _extension(dataset_filename) not in settings.allowed_dataset_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The dataset must be one of: {', '.join(settings.allowed_dataset_extensions)}.",
        )
    if task_type not in TASK_TYPES:
        raise AppError(ErrorCode.INVALID_TASK_TYPE, f"The task type must be one of: {', '.join(TASK_TYPES)}.")


def file_extension(filename: str) -> str:
    """Lower-case extension of a client-supplied filename (only used after validation)."""
    return _extension(filename)
