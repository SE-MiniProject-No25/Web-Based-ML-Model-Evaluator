"""Temporary Storage: saves uploads under server-generated names (SEC-02).

The client's filename never reaches the filesystem: files are stored as
``<uuid4><extension>`` where the extension comes from the allowlist. US-10
adds permissions, retention cleanup and stricter lifecycle handling.
"""

import re
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

_EXTENSION = re.compile(r"^\.[a-z0-9]{1,10}$")


class TemporaryStorage:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes | BinaryIO, extension: str) -> Path:
        """Store ``data`` under a fresh UUID name and return its path."""
        extension = extension.lower()
        if not _EXTENSION.match(extension):
            raise ValueError("extension must look like '.csv'")
        path = self.root / f"{uuid.uuid4().hex}{extension}"
        with open(path, "wb") as out:
            if isinstance(data, (bytes, bytearray)):
                out.write(data)
            else:
                shutil.copyfileobj(data, out)
        return path

    def delete(self, path: Path) -> None:
        """Remove a stored file; only files inside the storage root are touched."""
        resolved = Path(path).resolve()
        if self.root.resolve() not in resolved.parents:
            raise ValueError("path is outside the storage directory")
        resolved.unlink(missing_ok=True)
