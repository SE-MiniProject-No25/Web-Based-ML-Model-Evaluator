"""Input Validation Service.

Validates that all required fields are present, file extensions are allowed,
task types are supported, uploads comply with configured size limits (US-06),
models and datasets are well-formed (US-07), and target columns exist in the
dataset header (US-08). Keep ``validate_submission`` as the single entry point
called by the API.
"""

import atexit
import csv
import io
import subprocess
import sys
import tempfile
import threading
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from app.config import Settings
from app.errors import AppError, ErrorCode
from app.security import sanitized_env

TASK_TYPES = ("classification", "regression")
INSPECTOR_SCRIPT = str(Path(__file__).resolve().parent / "model_inspector.py")


def _start_inspector() -> subprocess.Popen:
    """A new, isolated inspector process. It imports scikit-learn, then waits for one model on stdin."""
    return subprocess.Popen(
        [sys.executable, INSPECTOR_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=tempfile.gettempdir(),
        env=sanitized_env(),
    )


class InspectorPool:
    """Keeps inspector processes started ahead of time (TEST-04, NFR-02).

    Starting Python and importing scikit-learn takes about 1.5 s, almost all of the time before the
    ``202``. Spares that have already done that are handed to the next requests, and a replacement is
    started straight away. Every model is still inspected in its own fresh process, used once, so the
    isolation is the same as starting one per request. Spares that are idle when the server exits see
    their stdin close and exit. With ``size`` spares, requests up to about ``size`` per 1.5 s get one
    that is ready; faster bursts wait for the import, as before.
    """

    def __init__(self, start=None, size: int = 2):
        self._start = start
        self._size = size
        self._spares: list[subprocess.Popen] = []
        self._lock = threading.Lock()

    def _new(self) -> subprocess.Popen:
        return (self._start or _start_inspector)()

    def _top_up(self) -> None:
        self._spares = [p for p in self._spares if p.poll() is None]
        while len(self._spares) < self._size:
            self._spares.append(self._new())

    def take(self) -> subprocess.Popen:
        """An inspector for one model: the oldest live spare, otherwise a new process.

        The replacement is started by ``replenish()`` once this check has finished, not now: a new
        process importing scikit-learn competes for the CPU with the check that is under way.
        """
        with self._lock:
            alive = [p for p in self._spares if p.poll() is None]
            process = alive.pop(0) if alive else self._new()
            self._spares = alive
            return process

    def replenish(self) -> None:
        """Start replacements for the spares that have been used."""
        with self._lock:
            self._top_up()

    def resize(self, size: int) -> None:
        self._size = max(size, 0)

    def warm(self) -> None:
        """Start the spares now, so the first requests do not wait for them."""
        with self._lock:
            self._top_up()

    def close(self) -> None:
        with self._lock:
            spares, self._spares = self._spares, []
        for process in spares:
            if process.poll() is None:
                process.kill()
                process.wait()


INSPECTORS = InspectorPool()
atexit.register(INSPECTORS.close)


def _extension(filename: str) -> str:
    return PurePosixPath(filename.replace("\\", "/")).suffix.lower()


def _enforce_file_size(file: BinaryIO, max_bytes: int, field_name: str) -> None:
    """Consume up to ``max_bytes + 1`` bytes and reject immediately if oversized.

    Stops reading as soon as the cumulative count exceeds ``max_bytes`` so
    unbounded uploads are never read in full. Preserves stream position
    (seek 0) upon success or failure.
    """
    total = 0
    chunk_size = 64 * 1024
    file.seek(0)
    try:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise AppError(
                    ErrorCode.FILE_TOO_LARGE,
                    f"The {field_name} file exceeds the maximum allowed size of {max_bytes} bytes.",
                )
    finally:
        file.seek(0)


def _validate_dataset_content(file: BinaryIO) -> list[str]:
    """Validate that the dataset is a non-empty, parseable, non-ragged CSV with a header (US-07)."""
    file.seek(0)
    try:
        content = file.read()
        if not content or not content.strip():
            raise AppError(ErrorCode.MALFORMED_DATASET, "The dataset file is empty.")

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file could not be parsed as UTF-8 text.",
            ) from None

        if "\x00" in text:
            raise AppError(ErrorCode.MALFORMED_DATASET, "The dataset file contains null bytes.")

        reader = csv.reader(io.StringIO(text))
        try:
            header = next(reader, None)
        except csv.Error:
            raise AppError(ErrorCode.MALFORMED_DATASET, "The dataset file is malformed.") from None

        if not header:
            raise AppError(ErrorCode.MALFORMED_DATASET, "The dataset file is missing a header row.")

        header_len = len(header)
        try:
            for row in reader:
                if not row:
                    continue
                if len(row) != header_len:
                    raise AppError(
                        ErrorCode.MALFORMED_DATASET,
                        "The dataset file contains ragged rows with inconsistent column counts.",
                    )
        except csv.Error:
            raise AppError(ErrorCode.MALFORMED_DATASET, "The dataset file is malformed.") from None
        return header
    finally:
        file.seek(0)


def _validate_model_content(file: BinaryIO, settings: Settings) -> None:
    """Inspect model in an isolated child process to verify it loads and has a callable predict (US-07).

    Security Notice:
    Deserializing untrusted pickle/joblib objects executes arbitrary bytecode.
    This validation runs in a separate child process with a timeout and sanitized
    environment to isolate the web server from memory corruption, hangs, or interpreter crashes.
    LIMITATION: This is process isolation, not an unprivileged container sandbox.
    """
    file.seek(0)
    try:
        proc = INSPECTORS.take()

        try:
            try:
                chunk_size = 64 * 1024
                total_written = 0
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    total_written += len(chunk)
                    if total_written > settings.max_upload_bytes:
                        raise AppError(
                            ErrorCode.FILE_TOO_LARGE,
                            f"The model file exceeds the limit of {settings.max_upload_bytes} bytes.",
                        )
                    proc.stdin.write(chunk)
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                # Child process exited early (e.g. invalid header, corrupted file, or crash)
                pass

            try:
                returncode = proc.wait(timeout=15.0)
            except subprocess.TimeoutExpired:
                raise AppError(
                    ErrorCode.INVALID_MODEL,
                    "The model file could not be loaded or is corrupted.",
                ) from None
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            INSPECTORS.replenish()

        if returncode == 1:
            raise AppError(
                ErrorCode.INVALID_MODEL,
                "The model file could not be loaded or is corrupted.",
            )
        elif returncode == 2:
            raise AppError(
                ErrorCode.INVALID_MODEL,
                "The model file must have a callable predict method.",
            )
        elif returncode != 0:
            raise AppError(
                ErrorCode.INVALID_MODEL,
                "The model file could not be loaded or is corrupted.",
            )
    finally:
        file.seek(0)


def validate_submission(
    *,
    model_filename: str | None,
    dataset_filename: str | None,
    task_type: str | None,
    target_column: str | None,
    settings: Settings,
    model_file: BinaryIO | None = None,
    dataset_file: BinaryIO | None = None,
) -> None:
    """Raise an ``AppError`` (Architecture section 11) if the submission must be rejected."""
    missing = [
        name
        for name, value in (
            ("model", model_filename),
            ("dataset", dataset_filename),
            ("task_type", task_type),
            ("target_column", target_column),
        )
        if not value or not value.strip()
    ]
    if missing:
        raise AppError(ErrorCode.MISSING_REQUIRED_FIELD, f"Missing required field(s): {', '.join(missing)}.")

    if _extension(model_filename) not in settings.allowed_model_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The model must be one of: {', '.join(settings.allowed_model_extensions)}.",
        )
    if _extension(dataset_filename) not in settings.allowed_dataset_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The dataset must be one of: {', '.join(settings.allowed_dataset_extensions)}.",
        )
    if task_type not in TASK_TYPES:
        raise AppError(ErrorCode.INVALID_TASK_TYPE, f"The task type must be one of: {', '.join(TASK_TYPES)}.")

    if model_file is not None:
        _enforce_file_size(model_file, settings.max_upload_bytes, "model")
        _validate_model_content(model_file, settings)
    if dataset_file is not None:
        _enforce_file_size(dataset_file, settings.max_upload_bytes, "dataset")
        header = _validate_dataset_content(dataset_file)
        if target_column not in header:
            raise AppError(
                ErrorCode.INVALID_TARGET_COLUMN,
                f"The selected target column '{target_column}' does not exist in the dataset.",
            )


def file_extension(filename: str) -> str:
    """Lower-case extension of a client-supplied filename (only used after validation)."""
    return _extension(filename)
