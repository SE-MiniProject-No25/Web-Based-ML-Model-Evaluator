"""Metrics Service.

PLACEHOLDER until US-19 (classification) and US-20 (regression) land: it only
keeps the interface the evaluation runner depends on, ``compute(task_type,
y_true, y_pred) -> dict``. Replace the body, keep the signature.
"""

from collections.abc import Sequence


def compute(task_type: str, y_true: Sequence, y_pred: Sequence) -> dict:
    """Return the metrics for the predictions (placeholder: only the sample count)."""
    return {"samples": len(y_true)}
