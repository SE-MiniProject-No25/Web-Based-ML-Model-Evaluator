"""Result Service: the one place that creates, updates and returns evaluations (FR-18, NFR-08).

The API and the evaluation runner both go through this service, so they always
agree on an evaluation's status and results. Records live in an in-memory store
behind a small interface; swap the store to persist them.
"""

import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from app.errors import AppError, ErrorCode


class Status(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


TERMINAL_STATUSES = frozenset({Status.COMPLETED, Status.FAILED})

# A status can only move forward along these edges; terminal statuses have none.
_ALLOWED_TRANSITIONS = {
    Status.PENDING: {Status.RUNNING},
    Status.RUNNING: {Status.COMPLETED, Status.FAILED},
    Status.COMPLETED: set(),
    Status.FAILED: set(),
}


class InvalidTransition(Exception):
    """An internal bug: something tried to move an evaluation to a status it cannot reach."""


@dataclass
class Evaluation:
    id: str
    task_type: str
    target_column: str
    model_filename: str
    dataset_filename: str
    created_at: datetime
    status: Status = Status.PENDING
    metrics: dict | None = None
    error: dict | None = None
    finished_at: datetime | None = None
    # Server-side artifact locations; never exposed through the API.
    model_path: Path | None = field(default=None, repr=False)
    dataset_path: Path | None = field(default=None, repr=False)

    def move_to(self, new_status: Status) -> None:
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransition(f"{self.status.value} -> {new_status.value}")
        self.status = new_status
        if new_status in TERMINAL_STATUSES:
            self.finished_at = datetime.now(UTC)


class EvaluationStore(Protocol):
    """What the Result Service needs from a store."""

    def add(self, evaluation: Evaluation) -> None: ...

    def get(self, evaluation_id: str) -> Evaluation | None: ...

    def update(self, evaluation_id: str, change: Callable[[Evaluation], None]) -> Evaluation | None: ...


class InMemoryEvaluationStore:
    """Thread-safe store. Callers only ever see copies, so records cannot be mutated from outside."""

    def __init__(self):
        self._records: dict[str, Evaluation] = {}
        self._lock = threading.Lock()

    def add(self, evaluation: Evaluation) -> None:
        with self._lock:
            self._records[evaluation.id] = evaluation

    def get(self, evaluation_id: str) -> Evaluation | None:
        with self._lock:
            record = self._records.get(evaluation_id)
            return replace(record) if record else None

    def update(self, evaluation_id: str, change: Callable[[Evaluation], None]) -> Evaluation | None:
        """Apply ``change`` to the record while holding the lock, so check-and-set is atomic."""
        with self._lock:
            record = self._records.get(evaluation_id)
            if record is None:
                return None
            change(record)
            return replace(record)


class ResultService:
    def __init__(self, store: EvaluationStore | None = None):
        self._store = store or InMemoryEvaluationStore()

    def create(
        self,
        task_type: str,
        target_column: str,
        model_filename: str,
        dataset_filename: str,
        model_path: Path | None = None,
        dataset_path: Path | None = None,
    ) -> Evaluation:
        """Store a new ``pending`` evaluation under a random, unguessable UUID."""
        evaluation = Evaluation(
            id=str(uuid.uuid4()),
            task_type=task_type,
            target_column=target_column,
            model_filename=model_filename,
            dataset_filename=dataset_filename,
            created_at=datetime.now(UTC),
            model_path=model_path,
            dataset_path=dataset_path,
        )
        self._store.add(evaluation)
        return replace(evaluation)

    def get(self, evaluation_id: str) -> Evaluation:
        """Return the evaluation, or raise ``EVALUATION_NOT_FOUND`` (404 at the API)."""
        evaluation = self._store.get(evaluation_id)
        if evaluation is None:
            raise AppError(ErrorCode.EVALUATION_NOT_FOUND, "Evaluation not found.")
        return evaluation

    def mark_running(self, evaluation_id: str) -> Evaluation:
        return self._update(evaluation_id, lambda e: e.move_to(Status.RUNNING))

    def mark_completed(self, evaluation_id: str, metrics: dict) -> Evaluation:
        def change(evaluation: Evaluation) -> None:
            evaluation.move_to(Status.COMPLETED)
            evaluation.metrics = metrics

        return self._update(evaluation_id, change)

    def mark_failed(self, evaluation_id: str, code: ErrorCode, message: str) -> Evaluation:
        """Fail the evaluation with a safe error object (``code``, ``message``)."""

        def change(evaluation: Evaluation) -> None:
            evaluation.move_to(Status.FAILED)
            evaluation.error = AppError(code, message).to_dict()

        return self._update(evaluation_id, change)

    def _update(self, evaluation_id: str, change: Callable[[Evaluation], None]) -> Evaluation:
        evaluation = self._store.update(evaluation_id, change)
        if evaluation is None:
            raise AppError(ErrorCode.EVALUATION_NOT_FOUND, "Evaluation not found.")
        return evaluation
