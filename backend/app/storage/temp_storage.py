"""Temporary Storage: saves uploads under server-generated names (SEC-02).

The client's filename never reaches the filesystem: files are stored as
``<uuid4><extension>`` where the extension comes from the allowlist. US-10
adds permissions, retention cleanup and stricter lifecycle handling.
"""

import logging
import os
import re
import shutil
import stat
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO

from app.storage.lifecycle import StorageLifecycleManager

logger = logging.getLogger(__name__)

_EXTENSION = re.compile(r"^\.[a-z0-9]{1,10}$")


class TemporaryStorage:
    """Manages isolated, server-named file storage with access controls and retention (SEC-02, SEC-07)."""

    def __init__(self, root: Path, retention_seconds: int = 3600):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        # Restrict directory access to the application user (Architecture §6.1, AC 3)
        self._set_restrictive_dir_permissions(self.root)
        self.retention_seconds = retention_seconds
        self.lifecycle = StorageLifecycleManager(self, retention_seconds=retention_seconds)

    @staticmethod
    def _set_restrictive_dir_permissions(path: Path) -> None:
        """Set 0o700 (rwx------) permissions on directory (POSIX only; safe on Windows)."""
        try:
            os.chmod(path, stat.S_IRWXU)
        except OSError:
            pass

    @staticmethod
    def _set_restrictive_file_permissions(path: Path) -> None:
        """Set 0o600 (rw-------) permissions on file (POSIX only; safe on Windows)."""
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    def save(self, data: bytes | BinaryIO, extension: str) -> Path:
        """Store ``data`` under a fresh UUID name with restrictive permissions and return its path."""
        extension = extension.lower()
        if not _EXTENSION.match(extension):
            raise ValueError("extension must look like '.csv'")
        filename = f"{uuid.uuid4().hex}{extension}"
        path = (self.root / filename).resolve()
        if self.root not in path.parents:
            raise ValueError("resolved path is outside the storage directory")

        # Open file with restrictive 0o600 creation flags
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        fd = os.open(path, flags, stat.S_IRUSR | stat.S_IWUSR)
        try:
            with open(fd, "wb", closefd=True) as out:
                if isinstance(data, (bytes, bytearray)):
                    out.write(data)
                else:
                    shutil.copyfileobj(data, out)
        except Exception:
            try:
                os.unlink(path)
            except OSError:
                pass
            raise

        self._set_restrictive_file_permissions(path)
        return path

    def delete(self, path: Path) -> None:
        """Remove a stored file; only files inside the storage root are touched."""
        resolved = Path(path).resolve()
        if self.root not in resolved.parents:
            raise ValueError("path is outside the storage directory")
        if resolved.is_dir():
            raise ValueError("cannot delete a directory")
        resolved.unlink(missing_ok=True)

    def cleanup_expired(
        self,
        max_age_seconds: int | None = None,
        active_paths: Iterable[Path | str | None] | None = None,
    ) -> list[Path]:
        """Delegate retention cleanup to StorageLifecycleManager."""
        return self.lifecycle.cleanup_expired(max_age_seconds, active_paths=active_paths)

    def delete_evaluation_artifacts(self, *paths: Path | str | None) -> list[Path]:
        """Delegate explicit artifact deletion to StorageLifecycleManager."""
        return self.lifecycle.delete_evaluation_artifacts(*paths)
