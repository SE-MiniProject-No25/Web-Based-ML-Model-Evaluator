"""Unit tests for the Input Validation Service (US-06, US-07, US-08): dataset parsing and how the
child process that inspects a model is handled (timeouts, broken pipes, exit statuses)."""

import io
import subprocess
from pathlib import Path

import pytest

from app.config import Settings
from app.errors import AppError, ErrorCode
from app.validation import service

COULD_NOT_LOAD = "The model file could not be loaded or is corrupted."
NO_PREDICT = "The model file must have a callable predict method."


def error_of(call) -> AppError:
    with pytest.raises(AppError) as raised:
        call()
    return raised.value


# --- the dataset ---------------------------------------------------------------------------------


def test_a_good_csv_returns_its_header():
    assert service._validate_dataset_content(io.BytesIO(b"a,b,label\n1,2,0\n3,4,1\n")) == ["a", "b", "label"]


def test_blank_lines_between_rows_are_ignored():
    assert service._validate_dataset_content(io.BytesIO(b"a,b\n\n1,2\n\n3,4\n")) == ["a", "b"]


def test_a_blank_first_line_means_there_is_no_header():
    error = error_of(lambda: service._validate_dataset_content(io.BytesIO(b"\n1,2\n")))
    assert error.code is ErrorCode.MALFORMED_DATASET
    assert "header" in error.message


def test_a_field_too_large_for_the_csv_parser_in_the_header_is_malformed():
    huge = b"a" * 200_000
    error = error_of(lambda: service._validate_dataset_content(io.BytesIO(huge + b",b\n1,2\n")))
    assert (error.code, error.message) == (ErrorCode.MALFORMED_DATASET, "The dataset file is malformed.")


def test_a_field_too_large_for_the_csv_parser_in_a_row_is_malformed():
    huge = b"a" * 200_000
    error = error_of(lambda: service._validate_dataset_content(io.BytesIO(b"a,b\n" + huge + b",2\n")))
    assert (error.code, error.message) == (ErrorCode.MALFORMED_DATASET, "The dataset file is malformed.")


def test_the_stream_is_rewound_after_checking_so_it_can_be_stored():
    stream = io.BytesIO(b"a,b\n1,2\n")
    service._validate_dataset_content(stream)
    assert stream.read() == b"a,b\n1,2\n"


# --- the child process that inspects a model ------------------------------------------------------


class FakeStdin:
    def __init__(self, broken=False):
        self.broken, self.received = broken, b""

    def write(self, chunk):
        if self.broken:
            raise BrokenPipeError
        self.received += chunk

    def close(self):
        pass


class FakeProcess:
    """Stands in for the inspector child process."""

    def __init__(self, returncode=0, hangs=False, broken_pipe=False):
        self.returncode_when_done = returncode
        self.hangs = hangs
        self.killed = False
        self.stdin = FakeStdin(broken=broken_pipe)

    def wait(self, timeout=None):
        if self.hangs and not self.killed:
            raise subprocess.TimeoutExpired("inspector", timeout)
        return self.returncode_when_done

    def poll(self):
        return None if (self.hangs and not self.killed) else self.returncode_when_done

    def kill(self):
        self.killed = True


@pytest.fixture
def child(monkeypatch):
    """Install a fake child process and return it."""

    def install(**options):
        process = FakeProcess(**options)
        monkeypatch.setattr(service, "INSPECTORS", service.InspectorPool(start=lambda: process))
        return process

    return install


def inspect(data=b"model bytes"):
    return service._validate_model_content(io.BytesIO(data), Settings())


def test_a_child_that_accepts_the_model_means_the_model_is_valid(child):
    process = child(returncode=0)
    inspect(b"model bytes")
    assert process.stdin.received == b"model bytes"  # the upload is streamed to the child


def test_exit_status_one_means_the_model_cannot_be_loaded(child):
    child(returncode=1)
    error = error_of(inspect)
    assert (error.code, error.message) == (ErrorCode.INVALID_MODEL, COULD_NOT_LOAD)


def test_exit_status_two_means_the_model_has_no_predict(child):
    child(returncode=2)
    error = error_of(inspect)
    assert (error.code, error.message) == (ErrorCode.INVALID_MODEL, NO_PREDICT)


def test_any_unexpected_exit_status_is_treated_as_an_unusable_model(child):
    child(returncode=3)
    assert error_of(inspect).code is ErrorCode.INVALID_MODEL


def test_a_child_that_exits_early_is_not_a_server_error(child):
    """If the child quits before reading everything, writing to it fails; the exit status decides."""
    child(returncode=1, broken_pipe=True)
    assert error_of(inspect).code is ErrorCode.INVALID_MODEL


def test_a_child_that_hangs_is_killed_and_the_model_rejected(child):
    process = child(hangs=True)

    error = error_of(inspect)

    assert error.code is ErrorCode.INVALID_MODEL
    assert process.killed, "a hung child must not be left running"


def test_a_model_larger_than_the_limit_is_rejected_while_streaming(child):
    child(returncode=0)
    small_limit = Settings(max_upload_bytes=10)
    error = error_of(lambda: service._validate_model_content(io.BytesIO(b"x" * 100), small_limit))
    assert error.code is ErrorCode.FILE_TOO_LARGE


# --- the spare inspector (TEST-04) -----------------------------------------------------------------


class Started:
    """A stand-in process that records whether it is alive."""

    count = 0

    def __init__(self):
        Started.count += 1
        self.number = Started.count
        self.exited = None
        self.killed = False

    def poll(self):
        return self.exited

    def kill(self):
        self.killed = True
        self.exited = -9

    def wait(self, timeout=None):
        return self.exited


def test_each_model_gets_a_fresh_process_and_a_new_spare_is_started_at_once():
    pool = service.InspectorPool(start=Started, size=2)
    pool.warm()
    first_spares = list(pool._spares)

    taken = [pool.take(), pool.take(), pool.take()]

    assert taken[:2] == first_spares  # oldest first, so the one that has waited longest
    assert len({id(p) for p in taken}) == 3  # never reused
    assert len(pool._spares) == 2  # topped up after every take


def test_a_spare_that_died_is_replaced():
    pool = service.InspectorPool(start=Started, size=1)
    pool.warm()
    dead = pool._spares[0]
    dead.exited = 1

    assert pool.take() is not dead


def test_with_no_spares_each_request_starts_its_own_process():
    pool = service.InspectorPool(start=Started, size=2)
    pool.resize(0)
    pool.warm()

    assert pool._spares == []
    assert pool.take() is not pool.take()


def test_warming_twice_keeps_the_same_spares_and_closing_kills_them():
    pool = service.InspectorPool(start=Started, size=2)
    pool.warm()
    spares = list(pool._spares)
    pool.warm()
    assert pool._spares == spares

    spares[1].exited = 0  # one already finished on its own
    pool.close()
    assert spares[0].killed and not spares[1].killed and pool._spares == []


def test_a_real_spare_inspector_checks_a_model():
    pool = service.InspectorPool()
    try:
        pool.warm()
        process = pool.take()
        model = (Path(__file__).parent / "fixtures" / "classification" / "model.joblib").read_bytes()
        process.communicate(model, timeout=60)
        assert process.returncode == 0
    finally:
        pool.close()
