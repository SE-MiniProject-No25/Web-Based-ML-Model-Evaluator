"""Application configuration: the single place that holds the limits and switches.

Defaults can be overridden with ``MLEVAL_*`` environment variables. The
Security/Policy Module and the Validation Service read their limits from here.
"""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

MODEL_EXTENSIONS = (".joblib", ".pkl")
DATASET_EXTENSIONS = (".csv",)


@dataclass(frozen=True)
class Settings:
    # Allowed upload extensions, lower-case with the leading dot.
    allowed_model_extensions: tuple = MODEL_EXTENSIONS
    allowed_dataset_extensions: tuple = DATASET_EXTENSIONS
    # Largest accepted upload, per file.
    max_upload_bytes: int = 10 * 1024 * 1024
    # Wall-clock limit for one evaluation run.
    evaluation_timeout_seconds: int = 60
    # How long temporary artifacts are kept after an evaluation ends.
    retention_seconds: int = 3600
    # Authentication on evaluation and result endpoints (off by default).
    auth_enabled: bool = False
    # Where uploads are stored: outside the source tree, never user-named.
    storage_dir: Path = Path(tempfile.gettempdir()) / "ml-model-evaluator"

    @property
    def allowed_extensions(self) -> tuple:
        return self.allowed_model_extensions + self.allowed_dataset_extensions


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    """Build the settings from defaults plus ``MLEVAL_*`` environment overrides."""
    defaults = Settings()
    return Settings(
        max_upload_bytes=int(os.environ.get("MLEVAL_MAX_UPLOAD_BYTES", defaults.max_upload_bytes)),
        evaluation_timeout_seconds=int(
            os.environ.get("MLEVAL_EVALUATION_TIMEOUT_SECONDS", defaults.evaluation_timeout_seconds)
        ),
        retention_seconds=int(os.environ.get("MLEVAL_RETENTION_SECONDS", defaults.retention_seconds)),
        auth_enabled=_env_bool("MLEVAL_AUTH_ENABLED", defaults.auth_enabled),
        storage_dir=Path(os.environ.get("MLEVAL_STORAGE_DIR", defaults.storage_dir)),
    )
