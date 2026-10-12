"""Result Service: stores, retrieves and formats evaluation results."""

from app.results.formatting import format_status
from app.results.service import (
    Evaluation,
    EvaluationStore,
    InMemoryEvaluationStore,
    InvalidTransition,
    ResultService,
    Status,
)

__all__ = [
    "Evaluation",
    "EvaluationStore",
    "InMemoryEvaluationStore",
    "InvalidTransition",
    "ResultService",
    "Status",
    "format_status",
]
