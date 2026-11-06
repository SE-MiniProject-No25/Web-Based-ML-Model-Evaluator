"""Storage Lifecycle Manager: manages retention and cleanup of temporary artifacts (Architecture §3, SEC-07).

Temporary uploaded artifacts are removed according to the application's configured
retention policy after the evaluation lifecycle ends (FR-17, SEC-07, TC-18).
"""

import logging
import time
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage.temp_storage import TemporaryStorage

logger = logging.getLogger(__name__)


class StorageLifecycleManager:
    """Deletes temporary artifacts according to the configured retention policy (SEC-07)."""

    def __init__(self, storage: "TemporaryStorage", retention_seconds: int = 3600):
        self.storage = storage
        self.retention_seconds = retention_seconds

    def cleanup_expired(
        self,
        max_age_seconds: int | None = None,
        active_paths: Iterable[Path | str | None] | None = None,
    ) -> list[Path]:
        """Delete temporary artifacts older than max_age_seconds (defaults to retention_seconds).

        Files in ``active_paths`` are protected and will never be deleted regardless of age.
        Returns the list of deleted paths.
        """
        limit = self.retention_seconds if max_age_seconds is None else max_age_seconds
        if limit < 0:
            limit = 0

        protected: set[Path] = set()
        if active_paths is not None:
            for p in active_paths:
                if p is not None:
                    protected.add(Path(p).resolve())

        now = time.time()
        deleted: list[Path] = []

        if not self.storage.root.exists():
            return deleted

        for entry in self.storage.root.iterdir():
            if not entry.is_file():
                continue
            if entry.resolve() in protected:
                logger.debug("Skipping active evaluation artifact: %s", entry.name)
                continue
            try:
                mtime = entry.stat().st_mtime
                age = now - mtime
                if age >= limit:
                    self.storage.delete(entry)
                    deleted.append(entry)
                    logger.info(
                        "Deleted expired temporary artifact %s (age=%.1fs, limit=%ds)",
                        entry.name,
                        age,
                        limit,
                    )
            except OSError as exc:
                logger.warning("Failed to inspect or delete temporary artifact %s: %s", entry.name, exc)

        return deleted

    def delete_evaluation_artifacts(self, *paths: Path | str | None) -> list[Path]:
        """Delete specific artifacts associated with an evaluation when its lifecycle ends."""
        deleted: list[Path] = []
        for p in paths:
            if p is None:
                continue
            path_obj = Path(p)
            try:
                if path_obj.exists() and path_obj.is_file():
                    self.storage.delete(path_obj)
                    deleted.append(path_obj)
                    logger.info("Deleted evaluation artifact %s", path_obj.name)
            except (OSError, ValueError) as exc:
                logger.warning("Failed to delete evaluation artifact %s: %s", path_obj, exc)
        return deleted

    def cleanup_all(self) -> list[Path]:
        """Delete all temporary stored files (e.g. for complete teardown or testing)."""
        deleted: list[Path] = []
        if not self.storage.root.exists():
            return deleted

        for entry in self.storage.root.iterdir():
            if entry.is_file():
                try:
                    self.storage.delete(entry)
                    deleted.append(entry)
                except (OSError, ValueError) as exc:
                    logger.warning("Failed to delete %s: %s", entry.name, exc)
        return deleted
