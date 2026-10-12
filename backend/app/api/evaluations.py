"""Evaluation endpoints (Architecture section 10)."""

from pathlib import PurePosixPath
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile

from app.evaluation import run_evaluation
from app.results import format_status
from app.validation.service import file_extension, validate_submission

router = APIRouter(prefix="/api")


def _display_name(filename: str) -> str:
    """The client's filename without any directory part; stored for display only."""
    return PurePosixPath(filename.replace("\\", "/")).name


@router.post("/evaluations", status_code=202)
def submit_evaluation(
    request: Request,
    background_tasks: BackgroundTasks,
    model: Annotated[UploadFile | None, File()] = None,
    dataset: Annotated[UploadFile | None, File()] = None,
    task_type: Annotated[str | None, Form()] = None,
    target_column: Annotated[str | None, Form()] = None,
) -> dict:
    """Validate, store the uploads, create the evaluation and start it in the background."""
    state = request.app.state
    model_name = model.filename if model else None
    dataset_name = dataset.filename if dataset else None

    # Validate before anything is stored or created: invalid input creates no evaluation.
    validate_submission(
        model_filename=model_name,
        dataset_filename=dataset_name,
        task_type=task_type,
        target_column=target_column,
        settings=state.settings,
    )

    model_path = state.storage.save(model.file, file_extension(model_name))
    try:
        dataset_path = state.storage.save(dataset.file, file_extension(dataset_name))
    except Exception:
        state.storage.delete(model_path)
        raise

    evaluation = state.results.create(
        task_type=task_type,
        target_column=target_column,
        model_filename=_display_name(model_name),
        dataset_filename=_display_name(dataset_name),
        model_path=model_path,
        dataset_path=dataset_path,
    )
    background_tasks.add_task(run_evaluation, evaluation.id, state.results)
    return {"evaluation_id": evaluation.id, "status": evaluation.status.value}


@router.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: str, request: Request) -> dict:
    """Current status; metrics when completed, the error object when failed (FR-12, FR-13, FR-19)."""
    # An unknown ID raises EVALUATION_NOT_FOUND, which the error handler turns into a 404.
    return format_status(request.app.state.results.get(evaluation_id))
