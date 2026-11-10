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
    # Address-space limit for one evaluation. Enforced on Linux and macOS only; Windows has no
    # equivalent for a plain child process, so there only the time limit applies.
    evaluation_memory_limit_bytes: int = 2 * 1024 * 1024 * 1024
    # Model inspector processes kept ready, with scikit-learn imported, so a submission is acknowledged
    # quickly (each model is still checked in its own fresh process). 0 starts one per request.
    spare_inspectors: int = 2
    # How long temporary artifacts are kept after an evaluation ends.
    retention_seconds: int = 3600
    # Authentication on evaluation and result endpoints (off by default).
    auth_enabled: bool = False
    # Secret API key required when auth_enabled is True (loaded from MLEVAL_API_KEY).
    api_key: str | None = None
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
        evaluation_memory_limit_bytes=int(
            os.environ.get("MLEVAL_EVALUATION_MEMORY_LIMIT_BYTES", defaults.evaluation_memory_limit_bytes)
        ),
        retention_seconds=int(os.environ.get("MLEVAL_RETENTION_SECONDS", defaults.retention_seconds)),
        spare_inspectors=int(os.environ.get("MLEVAL_SPARE_INSPECTORS", defaults.spare_inspectors)),
        auth_enabled=_env_bool("MLEVAL_AUTH_ENABLED", defaults.auth_enabled),
        api_key=os.environ.get("MLEVAL_API_KEY", defaults.api_key),
        storage_dir=Path(os.environ.get("MLEVAL_STORAGE_DIR", defaults.storage_dir)),
    )
