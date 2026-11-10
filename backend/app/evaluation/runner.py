"""Evaluation runner: runs the model in an isolated process and scores it (FR-08, FR-12, FR-14, SEC-04).

Meant to run as a background task after the ``202`` response. All progress goes through the Result
Service, so the API always sees a consistent status.

The model is never loaded in the server process: ``joblib.load`` executes code contained in the
file. ``worker.py`` loads it and predicts in a child process with a sanitized environment, the
configured time limit and the configured memory limit (set by the worker itself on Linux and macOS,
and by a Windows job object on Windows). Scoring then happens
here, on plain lists, with the trusted Metrics Service.

Failure outcomes (Architecture section 11):

- the dataset's columns do not match the model      -> ``INCOMPATIBLE_INPUTS``
- the time or memory limit is exceeded               -> ``RESOURCE_LIMIT_EXCEEDED``
- anything else (crash, bad file, metrics error)     -> ``EVALUATION_FAILED``

Only safe messages reach the client; tracebacks are logged on the server.
"""

import json
import logging
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.config import Settings
from app.errors import ErrorCode
from app.metrics import compute
from app.results import Evaluation, ResultService
from app.security import limit_child_memory, sanitized_env

logger = logging.getLogger(__name__)

WORKER_PATH = Path(__file__).resolve().parent / "worker.py"

# Shown to the client for any unexpected failure; details go to the server log only (SEC-05).
GENERIC_FAILURE_MESSAGE = "The evaluation could not be completed."

MetricsFn = Callable[..., dict]  # (task_type, y_true, y_pred) -> metrics

_MAX_NAMES = 5
_MAX_NAME_LENGTH = 50


class _Failure(Exception):
    """An evaluation outcome that ends as ``failed`` with a safe code and message."""

    def __init__(self, code: ErrorCode, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def run_evaluation(
    evaluation_id: str,
    results: ResultService,
    metrics_fn: MetricsFn = compute,
    settings: Settings | None = None,
) -> None:
    """Run one evaluation to a terminal status (``completed`` or ``failed``)."""
    settings = settings or Settings()
    evaluation = results.mark_running(evaluation_id)
    try:
        predictions = _predict_in_child_process(evaluation, settings)
        y_true = np.asarray(predictions["y_true"])
        y_pred = np.asarray(predictions["y_pred"])
        metrics = metrics_fn(evaluation.task_type, y_true, y_pred)
    except _Failure as failure:
        results.mark_failed(evaluation_id, failure.code, failure.message)
        return
    except Exception:
        logger.exception("Evaluation %s failed", evaluation_id)
        results.mark_failed(evaluation_id, ErrorCode.EVALUATION_FAILED, GENERIC_FAILURE_MESSAGE)
        return
    results.mark_completed(evaluation_id, metrics)


def _predict_in_child_process(evaluation: Evaluation, settings: Settings) -> dict:
    with tempfile.TemporaryDirectory() as workdir:
        result_path = Path(workdir) / "result.json"
        command = [
            sys.executable,
            str(WORKER_PATH),
            str(evaluation.model_path),
            str(evaluation.dataset_path),
            evaluation.target_column,
            str(result_path),
            str(settings.evaluation_memory_limit_bytes),
        ]
        process = subprocess.Popen(
            command,
            env=sanitized_env(),
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Windows: the operating system enforces the memory limit (on Linux and macOS the worker does).
        memory_limit = limit_child_memory(process, settings.evaluation_memory_limit_bytes)
        try:
            _, stderr = process.communicate(timeout=settings.evaluation_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            limit = settings.evaluation_timeout_seconds
            logger.warning("Evaluation %s exceeded the %ss time limit", evaluation.id, limit)
            raise _Failure(
                ErrorCode.RESOURCE_LIMIT_EXCEEDED,
                f"The evaluation exceeded the time limit of {limit} seconds and was stopped.",
            ) from None
        finally:
            if memory_limit is not None:
                memory_limit.close()

        if stderr:
            # Tracebacks from the child: server-side only.
            logger.error("Evaluation %s worker output:\n%s", evaluation.id, stderr[-4000:])

        if not result_path.exists():
            # The child crashed or was killed (for example by the OS) before reporting.
            status = process.returncode
            logger.error("Evaluation %s worker exited with status %s without a result", evaluation.id, status)
            raise _Failure(ErrorCode.EVALUATION_FAILED, GENERIC_FAILURE_MESSAGE)

        outcome = json.loads(result_path.read_text(encoding="utf-8"))

    if outcome.get("ok") is True:
        return outcome
    raise _failure_from(outcome)


def _failure_from(outcome: dict) -> _Failure:
    """Turn the worker's report into a safe failure; unknown codes become the generic failure."""
    code = outcome.get("code")
    if code == ErrorCode.INCOMPATIBLE_INPUTS.value:
        return _Failure(ErrorCode.INCOMPATIBLE_INPUTS, _incompatible_message(outcome))
    if code == ErrorCode.RESOURCE_LIMIT_EXCEEDED.value:
        return _Failure(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED, "The evaluation exceeded the memory limit and was stopped."
        )
    return _Failure(ErrorCode.EVALUATION_FAILED, GENERIC_FAILURE_MESSAGE)


def _incompatible_message(outcome: dict) -> str:
    """Describe the mismatch using column names only, shortened (they come from the user's own files)."""
    if "expected_count" in outcome:
        return (
            f"The dataset has {outcome.get('given_count')} feature column(s) but the model expects "
            f"{outcome.get('expected_count')}."
        )
    parts = ["The dataset's columns do not match the features the model expects."]
    for key, label in (("missing", "Missing from the dataset"), ("extra", "Not used by the model")):
        names = [str(n)[:_MAX_NAME_LENGTH] for n in (outcome.get(key) or [])[:_MAX_NAMES]]
        if names:
            more = "…" if len(outcome.get(key) or []) > _MAX_NAMES else ""
            parts.append(f"{label}: {', '.join(names)}{more}.")
    return " ".join(parts)
