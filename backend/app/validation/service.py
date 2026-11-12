"""Inspect an uploaded model in a fresh isolated child process.

    Deserializing untrusted pickle/joblib files can execute arbitrary bytecode.
    Inspection runs in a separate process with a timeout and sanitized
    environment to isolate the web server from crashes, memory corruption,
    and hangs.

    LIMITATION: This is process isolation, not an unprivileged container
    sandbox. The child process retains the privileges of the host user.
"""

import atexit
import csv
import io
import logging
import subprocess
import sys
import tempfile
import threading
from pathlib import Path, PurePosixPath
from typing import BinaryIO

from app.config import Settings
from app.errors import AppError, ErrorCode
from app.security import sanitized_env

logger = logging.getLogger(__name__)

TASK_TYPES = ("classification", "regression")
INSPECTOR_SCRIPT = str(Path(__file__).resolve().parent / "model_inspector.py")


def _start_inspector() -> subprocess.Popen:
    """Start an isolated inspector and wait until its imports are ready."""
    proc = subprocess.Popen(
        [sys.executable, INSPECTOR_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=tempfile.gettempdir(),
        env=sanitized_env(),
    )

    ready_event = threading.Event()
    ready_line = []

    def read_ready() -> None:
        try:
            ready_line.append(proc.stdout.readline())
        finally:
            ready_event.set()

    reader = threading.Thread(target=read_ready, daemon=True)
    reader.start()

    if not ready_event.wait(timeout=30):
        proc.kill()
        proc.wait()
        proc.stdout.close()
        raise RuntimeError(
            "Model inspector did not become ready within 30 seconds."
        )

    if not ready_line or ready_line[0].strip() != b"READY":
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        proc.stdout.close()
        raise RuntimeError("Model inspector failed to initialize.")

    proc.stdout.close()
    proc.stdout = None

    return proc


class InspectorPool:
    """Keeps initialized, one-use inspector processes ready for submissions."""

    def __init__(self, start=None, size: int = 2):
        self._start = start
        self._size = size
        self._spares: list[subprocess.Popen] = []
        self._starting = 0
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _new(self) -> subprocess.Popen:
        return (self._start or _start_inspector)()

    def _top_up(self) -> None:
        """Start missing inspectors without holding the pool lock."""
        while True:
            with self._condition:
                self._spares = [
                    process
                    for process in self._spares
                    if process.poll() is None
                ]

                if len(self._spares) + self._starting >= self._size:
                    return

                self._starting += 1

            try:
                process = self._new()
            except Exception:
                with self._condition:
                    self._starting -= 1
                    self._condition.notify_all()
                raise

            with self._condition:
                self._starting -= 1

                if process.poll() is None:
                    self._spares.append(process)
                else:
                    logger.warning(
                        "A newly started inspector exited before becoming available."
                    )
                    self._condition.notify_all()
                    return

                self._condition.notify_all()

    def take(self) -> subprocess.Popen:
        """Take a ready inspector, waiting for an existing replacement if necessary."""
        while True:
            start_sync = False

            with self._condition:
                self._spares = [
                    process
                    for process in self._spares
                    if process.poll() is None
                ]

                if self._spares:
                    process = self._spares.pop(0)
                    break

                if self._size <= 0:
                    start_sync = True
                elif self._starting > 0:
                    self._condition.wait()
                    continue
                else:
                    self._starting += 1
                    start_sync = True

            if start_sync:
                try:
                    process = self._new()
                finally:
                    with self._condition:
                        self._starting -= 1
                        self._condition.notify_all()

                break

        return process

    def _replenish(self) -> None:
        try:
            self._top_up()
        except Exception:
            logger.exception(
                "Could not replenish the model inspector pool."
            )

    def replenish(self) -> None:
        """Synchronously replenish the pool."""
        self._replenish()

    def replenish_async(self) -> None:
        """Replenish the pool in a background thread."""
        threading.Thread(
            target=self._replenish,
            daemon=True,
        ).start()

    def resize(self, size: int) -> None:
        with self._condition:
            self._size = max(size, 0)
            self._condition.notify_all()

    def warm(self) -> None:
        """Initialize the initial pool before accepting requests."""
        self._top_up()

    def close(self) -> None:
        with self._condition:
            spares, self._spares = self._spares, []

        for process in spares:
            if process.poll() is None:
                process.kill()
                process.wait()


INSPECTORS = InspectorPool()
atexit.register(INSPECTORS.close)


def _extension(filename: str) -> str:
    return PurePosixPath(filename.replace("\\", "/")).suffix.lower()


def _enforce_file_size(
    file: BinaryIO,
    max_bytes: int,
    field_name: str,
) -> None:
    """Read at most max_bytes + 1 bytes and preserve the stream position."""
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
                    f"The {field_name} file exceeds the maximum allowed size "
                    f"of {max_bytes} bytes.",
                )
    finally:
        file.seek(0)


def _validate_dataset_content(file: BinaryIO) -> list[str]:
    """Validate a non-empty, parseable, non-ragged CSV dataset."""
    file.seek(0)

    try:
        content = file.read()

        if not content or not content.strip():
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file is empty.",
            )

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file could not be parsed as UTF-8 text.",
            ) from None

        if "\x00" in text:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file contains null bytes.",
            )

        reader = csv.reader(io.StringIO(text))

        try:
            header = next(reader, None)
        except csv.Error:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file is malformed.",
            ) from None

        if not header:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file is missing a header row.",
            )

        if len(header) == 1:
            separators = ((";", "semicolons"), ("\t", "tabs"))
            separator = next(
                (name for sep, name in separators if sep in header[0]),
                None,
            )

            if separator:
                raise AppError(
                    ErrorCode.MALFORMED_DATASET,
                    f"The dataset must be comma-separated, but this file "
                    f"uses {separator}. Save it again as a comma-separated CSV.",
                )

        header_len = len(header)

        try:
            for row in reader:
                if not row:
                    continue

                if len(row) != header_len:
                    raise AppError(
                        ErrorCode.MALFORMED_DATASET,
                        "The dataset file contains ragged rows with "
                        "inconsistent column counts.",
                    )
        except csv.Error:
            raise AppError(
                ErrorCode.MALFORMED_DATASET,
                "The dataset file is malformed.",
            ) from None

        return header

    finally:
        file.seek(0)


def _validate_model_content(
    file: BinaryIO,
    settings: Settings,
) -> None:
    """Inspect an uploaded model in a fresh isolated child process."""
    file.seek(0)

    try:
        proc = INSPECTORS.take()

        # Begin replacement startup immediately after consuming a spare.
        INSPECTORS.replenish_async()

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
                            f"The model file exceeds the limit of "
                            f"{settings.max_upload_bytes} bytes.",
                        )

                    proc.stdin.write(chunk)

                proc.stdin.close()

            except (BrokenPipeError, OSError):
                # The child may have exited early due to invalid or corrupted input.
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
    """Raise an AppError if the submission must be rejected."""
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
        raise AppError(
            ErrorCode.MISSING_REQUIRED_FIELD,
            f"Missing required field(s): {', '.join(missing)}.",
        )

    if _extension(model_filename) not in settings.allowed_model_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The model must be one of: "
            f"{', '.join(settings.allowed_model_extensions)}.",
        )

    if _extension(dataset_filename) not in settings.allowed_dataset_extensions:
        raise AppError(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            f"The dataset must be one of: "
            f"{', '.join(settings.allowed_dataset_extensions)}.",
        )

    if task_type not in TASK_TYPES:
        raise AppError(
            ErrorCode.INVALID_TASK_TYPE,
            f"The task type must be one of: {', '.join(TASK_TYPES)}.",
        )

    if model_file is not None:
        _enforce_file_size(
            model_file,
            settings.max_upload_bytes,
            "model",
        )
        _validate_model_content(model_file, settings)

    if dataset_file is not None:
        _enforce_file_size(
            dataset_file,
            settings.max_upload_bytes,
            "dataset",
        )
        header = _validate_dataset_content(dataset_file)

        if target_column.strip() not in [
            name.strip() for name in header
        ]:
            raise AppError(
                ErrorCode.INVALID_TARGET_COLUMN,
                f"The selected target column '{target_column}' "
                "does not exist in the dataset.",
            )


def file_extension(filename: str) -> str:
    """Return the lower-case extension of a client-supplied filename."""
    return _extension(filename)
