"""Metrics Service for model evaluation.

Classification behaviour:
- Accuracy is always reported.
- Binary classification uses the positive class for precision, recall, and F1.
- Multiclass classification uses macro averaging so every class contributes
  equally regardless of class frequency.
- Undefined precision, recall, or F1 values are reported as 0.0 rather than
  raising an exception.

Regression metrics are implemented separately by US-20.
"""

from collections.abc import Sequence

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

CLASSIFICATION = "classification"
REGRESSION = "regression"


def compute(task_type: str, y_true: Sequence, y_pred: Sequence) -> dict[str, float]:
    """Compute metrics for the requested machine-learning task.

    Binary classification reports precision, recall, and F1 for the positive
    class. Multiclass classification reports their macro averages.

    Regression is intentionally not implemented here because it belongs to
    US-20.
    """
    if task_type == CLASSIFICATION:
        return _compute_classification(y_true, y_pred)

    if task_type == REGRESSION:
        return {}

    raise ValueError(f"Unsupported task type: {task_type}")


def _compute_classification(
    y_true: Sequence,
    y_pred: Sequence,
) -> dict[str, float]:
    """Compute standard binary or multiclass classification metrics."""
    labels = set(y_true) | set(y_pred)
    average = "binary" if len(labels) <= 2 else "macro"

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                average=average,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                average=average,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                average=average,
                zero_division=0,
            )
        ),
    }