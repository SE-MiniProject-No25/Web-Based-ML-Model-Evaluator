import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.errors import AppError, ErrorCode
from app.results import InvalidTransition, ResultService, Status


@pytest.fixture
def service():
    return ResultService()


def new(service):
    return service.create("classification", "label", "model.joblib", "data.csv")


def test_create_stores_a_pending_record_with_a_random_uuid(service):
    evaluation = new(service)
    assert uuid.UUID(evaluation.id).version == 4
    assert evaluation.status is Status.PENDING
    assert (evaluation.task_type, evaluation.target_column) == ("classification", "label")
    assert (evaluation.model_filename, evaluation.dataset_filename) == ("model.joblib", "data.csv")
    assert evaluation.created_at is not None
    assert evaluation.finished_at is None
    assert service.get(evaluation.id).id == evaluation.id


def test_ids_are_unique(service):
    assert len({new(service).id for _ in range(100)}) == 100


def test_unknown_id_is_not_found(service):
    with pytest.raises(AppError) as exc:
        service.get("does-not-exist")
    assert exc.value.code is ErrorCode.EVALUATION_NOT_FOUND
    assert exc.value.status_code == 404


def test_updating_an_unknown_id_is_not_found(service):
    with pytest.raises(AppError) as exc:
        service.mark_running("does-not-exist")
    assert exc.value.code is ErrorCode.EVALUATION_NOT_FOUND


def test_lifecycle_to_completed_stores_metrics_and_finish_time(service):
    evaluation = new(service)
    assert service.mark_running(evaluation.id).status is Status.RUNNING
    done = service.mark_completed(evaluation.id, {"accuracy": 0.9})
    assert done.status is Status.COMPLETED
    assert done.metrics == {"accuracy": 0.9}
    assert done.finished_at is not None
    assert service.get(evaluation.id).metrics == {"accuracy": 0.9}


def test_lifecycle_to_failed_stores_a_safe_error_object(service):
    evaluation = new(service)
    service.mark_running(evaluation.id)
    failed = service.mark_failed(evaluation.id, ErrorCode.EVALUATION_FAILED, "The evaluation failed.")
    assert failed.status is Status.FAILED
    assert failed.error == {"code": "EVALUATION_FAILED", "message": "The evaluation failed."}
    assert failed.metrics is None
    assert failed.finished_at is not None


@pytest.mark.parametrize("skip_running", [True, False])
def test_status_cannot_skip_or_move_backwards(service, skip_running):
    evaluation = new(service)
    if skip_running:
        with pytest.raises(InvalidTransition):
            service.mark_completed(evaluation.id, {})
        assert service.get(evaluation.id).status is Status.PENDING
    else:
        service.mark_running(evaluation.id)
        with pytest.raises(InvalidTransition):
            service.mark_running(evaluation.id)


@pytest.mark.parametrize("finish", ["completed", "failed"])
def test_a_terminal_status_never_changes(service, finish):
    evaluation = new(service)
    service.mark_running(evaluation.id)
    if finish == "completed":
        service.mark_completed(evaluation.id, {"r2": 1.0})
    else:
        service.mark_failed(evaluation.id, ErrorCode.EVALUATION_FAILED, "x")
    before = service.get(evaluation.id)

    for attempt in (
        lambda: service.mark_running(evaluation.id),
        lambda: service.mark_completed(evaluation.id, {"r2": 0.0}),
        lambda: service.mark_failed(evaluation.id, ErrorCode.INCOMPATIBLE_INPUTS, "y"),
    ):
        with pytest.raises(InvalidTransition):
            attempt()

    after = service.get(evaluation.id)
    assert (after.status, after.metrics, after.error, after.finished_at) == (
        before.status,
        before.metrics,
        before.error,
        before.finished_at,
    )


def test_returned_records_are_copies(service):
    evaluation = new(service)
    evaluation.status = Status.COMPLETED
    assert service.get(evaluation.id).status is Status.PENDING


def test_concurrent_creates_are_all_stored(service):
    with ThreadPoolExecutor(max_workers=16) as pool:
        ids = list(pool.map(lambda _: new(service).id, range(200)))
    assert len(set(ids)) == 200
    assert all(service.get(i).status is Status.PENDING for i in ids)


def test_concurrent_finishers_cannot_both_win(service):
    evaluation = new(service)
    service.mark_running(evaluation.id)

    def finish(i):
        try:
            service.mark_completed(evaluation.id, {"n": i})
            return True
        except InvalidTransition:
            return False

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(finish, range(50)))
    assert results.count(True) == 1
    assert service.get(evaluation.id).metrics == {"n": results.index(True)}
