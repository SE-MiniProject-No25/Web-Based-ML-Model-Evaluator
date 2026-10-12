"""Formats an evaluation into the status response of Architecture section 10.2."""

from app.results.service import Evaluation, Status


def format_status(evaluation: Evaluation) -> dict:
    """Public view: never includes server-side paths or original filenames."""
    body = {"evaluation_id": evaluation.id, "status": evaluation.status.value}
    if evaluation.status is Status.COMPLETED:
        body.update(task_type=evaluation.task_type, metrics=evaluation.metrics)
    elif evaluation.status is Status.FAILED:
        body.update(task_type=evaluation.task_type, error=evaluation.error)
    return body
