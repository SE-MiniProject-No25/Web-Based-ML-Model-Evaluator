"""Formats an evaluation for the status response (Architecture 10.2) and the downloadable result (10.3)."""

from app.results.service import Evaluation, Status


def format_status(evaluation: Evaluation) -> dict:
    """Public view: never includes server-side paths or original filenames."""
    body = {"evaluation_id": evaluation.id, "status": evaluation.status.value}
    if evaluation.status is Status.COMPLETED:
        body.update(task_type=evaluation.task_type, metrics=evaluation.metrics)
    elif evaluation.status is Status.FAILED:
        body.update(task_type=evaluation.task_type, error=evaluation.error)
    return body


def format_download(evaluation: Evaluation) -> dict:
    """The structured result file (FR-15): identity, inputs, metrics and timestamps.

    Only for completed evaluations. Includes the client's original filenames (directory part already
    removed) but never server-side paths.
    """
    return {
        "evaluation_id": evaluation.id,
        "status": evaluation.status.value,
        "task_type": evaluation.task_type,
        "target_column": evaluation.target_column,
        "model_filename": evaluation.model_filename,
        "dataset_filename": evaluation.dataset_filename,
        "metrics": evaluation.metrics,
        "created_at": evaluation.created_at.isoformat(),
        "finished_at": evaluation.finished_at.isoformat() if evaluation.finished_at else None,
    }
