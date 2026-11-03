"""Evaluation endpoints (Architecture section 10)."""

import json
from pathlib import PurePosixPath
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, Request, Response, UploadFile

from app.api.docs import DOWNLOAD_RESPONSES, FIELD_DESCRIPTIONS, STATUS_RESPONSES, SUBMIT_RESPONSES
from app.errors import AppError, ErrorCode
from app.evaluation import run_evaluation
from app.results import Status, format_download, format_status
from app.validation.service import file_extension, validate_submission

router = APIRouter(prefix="/api", tags=["evaluations"])


def _display_name(filename: str) -> str:
    """The client's filename without any directory part; stored for display only."""
    return PurePosixPath(filename.replace("\\", "/")).name


@router.post(
    "/evaluations",
    status_code=202,
    summary="Submit an evaluation",
    response_description="Accepted: the evaluation was created and is running in the background.",
    responses=SUBMIT_RESPONSES,
)
def submit_evaluation(
    request: Request,
    background_tasks: BackgroundTasks,
    model: Annotated[UploadFile | None, File(description=FIELD_DESCRIPTIONS["model"])] = None,
    dataset: Annotated[UploadFile | None, File(description=FIELD_DESCRIPTIONS["dataset"])] = None,
    task_type: Annotated[str | None, Form(description=FIELD_DESCRIPTIONS["task_type"])] = None,
    target_column: Annotated[str | None, Form(description=FIELD_DESCRIPTIONS["target_column"])] = None,
) -> dict:
    """Send the model, the dataset, the task type and the target column as `multipart/form-data`.

    All four fields are required (a missing one is answered with `400 MISSING_REQUIRED_FIELD`). The
    inputs are validated first; invalid input is rejected with the error from the table in the
    Architecture document and no evaluation is created. Valid input is accepted with `202` and the
    evaluation runs in the background.
    """
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
        model_file=model.file if model else None,
        dataset_file=dataset.file if dataset else None,
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
    background_tasks.add_task(run_evaluation, evaluation.id, state.results, settings=state.settings)
    return {"evaluation_id": evaluation.id, "status": evaluation.status.value}


@router.get(
    "/evaluations/{evaluation_id}",
    summary="Get an evaluation's status and results",
    responses=STATUS_RESPONSES,
)
def get_evaluation(evaluation_id: str, request: Request) -> dict:
    """The status is `pending`, `running`, `completed` or `failed`. Poll until it is `completed` or `failed`.

    A completed evaluation includes its metrics (accuracy, precision, recall and F1 for classification;
    MAE, MSE, RMSE and R² for regression). A failed one includes the `error` object instead.
    """
    # An unknown ID raises EVALUATION_NOT_FOUND, which the error handler turns into a 404.
    return format_status(request.app.state.results.get(evaluation_id))


@router.get(
    "/evaluations/{evaluation_id}/download",
    summary="Download a completed result as a file",
    responses=DOWNLOAD_RESPONSES,
)
def download_evaluation(evaluation_id: str, request: Request) -> Response:
    """The completed result as a JSON file.

    It contains the ID, task type, target column, input filenames, metrics and timestamps.

    Only available once the evaluation has completed; before that, or if it failed, the answer is
    `409 EVALUATION_NOT_COMPLETED` and no file is returned.
    """
    # An unknown ID raises EVALUATION_NOT_FOUND (404), as for the status endpoint (FR-19).
    evaluation = request.app.state.results.get(evaluation_id)

    if evaluation.status is not Status.COMPLETED:
        if evaluation.status is Status.FAILED:
            message = "The evaluation failed, so there are no results to download."
        else:
            message = "The evaluation has not finished yet. Try again when its status is completed."
        raise AppError(ErrorCode.EVALUATION_NOT_COMPLETED, message)

    # The ID is a server-generated UUID, so it is safe to use in the filename.
    return Response(
        content=json.dumps(format_download(evaluation), indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="evaluation-{evaluation.id}.json"'},
    )
