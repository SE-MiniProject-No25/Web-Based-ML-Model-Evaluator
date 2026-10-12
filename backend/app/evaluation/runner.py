"""Evaluation runner: loads the model, predicts on the dataset, hands off to metrics (FR-08, FR-12).

Meant to run as a background task after the ``202`` response. All progress goes
through the Result Service, so the API always sees a consistent status.

Security note: ``joblib.load`` executes code contained in the file. Only
validated inputs may reach this runner (Architecture section 6.1, boundary 2);
US-04 adds process isolation and the time limit.
"""

import logging
from collections.abc import Callable

import joblib
import pandas as pd

from app.errors import ErrorCode
from app.metrics import compute
from app.results import ResultService

logger = logging.getLogger(__name__)

# Shown to the client for any failure; details go to the server log only (SEC-05).
GENERIC_FAILURE_MESSAGE = "The evaluation could not be completed."

MetricsFn = Callable[..., dict]  # (task_type, y_true, y_pred) -> metrics


def run_evaluation(evaluation_id: str, results: ResultService, metrics_fn: MetricsFn = compute) -> None:
    """Run one evaluation to a terminal status (``completed`` or ``failed``)."""
    evaluation = results.mark_running(evaluation_id)
    try:
        model = joblib.load(evaluation.model_path)
        dataset = pd.read_csv(evaluation.dataset_path)

        y_true = dataset[evaluation.target_column].to_numpy()
        features = dataset.drop(columns=[evaluation.target_column])
        y_pred = model.predict(features)

        metrics = metrics_fn(evaluation.task_type, y_true, y_pred)
    except Exception:
        logger.exception("Evaluation %s failed", evaluation_id)
        results.mark_failed(evaluation_id, ErrorCode.EVALUATION_FAILED, GENERIC_FAILURE_MESSAGE)
        return
    results.mark_completed(evaluation_id, metrics)
