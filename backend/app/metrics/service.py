"""Metrics Service for model evaluation.

Classification behaviour:
- Accuracy is always reported.
- Binary classification uses the positive class for precision, recall, and F1.
- Multiclass classification uses macro averaging so every class contributes
  equally regardless of class frequency.
- Undefined precision, recall, or F1 values are reported as 0.0.

Regression behaviour:
- MAE, MSE, RMSE, and R² are reported.
- R² values that are undefined for the supplied targets are represented as
  0.0 so evaluation completes without returning a non-finite metric.
"""

from collections.abc import Sequence
from math import isfinite, sqrt

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

CLASSIFICATION = "classification"
REGRESSION = "regression"


def compute(task_type: str, y_true: Sequence, y_pred: Sequence) -> dict[str, float]:
    """Compute metrics for the requested machine-learning task."""
    if task_type == CLASSIFICATION:
        return _compute_classification(y_true, y_pred)

    if task_type == REGRESSION:
        return _compute_regression(y_true, y_pred)

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


def _compute_regression(
    y_true: Sequence,
    y_pred: Sequence,
) -> dict[str, float]:
    """Compute MAE, MSE, RMSE, and R² regression metrics."""
    mse = float(mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    if not isfinite(r2):
        r2 = 0.0

    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": mse,
        "rmse": sqrt(mse),
        "r2": r2,
    }