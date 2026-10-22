"""Generate the shared deterministic reference fixtures for EN-02.

The generated files are used by the Metrics Service and integration tests.
Running this script again recreates the same logical models, datasets, and
expected metric values.

Run from the backend directory with:

    python tests/generate_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CLASSIFICATION_DIR = FIXTURES_DIR / "classification"
REGRESSION_DIR = FIXTURES_DIR / "regression"
NEGATIVE_DIR = FIXTURES_DIR / "negative"

CLASSIFICATION_TARGET = "label"
REGRESSION_TARGET = "price"


def _prepare_directories() -> None:
    """Create all fixture directories if they do not already exist."""
    CLASSIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    REGRESSION_DIR.mkdir(parents=True, exist_ok=True)
    NEGATIVE_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, values: dict[str, float]) -> None:
    """Write metric values using a stable, human-readable JSON format."""
    path.write_text(
        json.dumps(values, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def generate_classification_fixture() -> None:
    """Generate a deterministic binary-classification reference fixture."""
    rng = np.random.default_rng(2026)

    features = pd.DataFrame(
        {
            "feature_a": rng.normal(size=80),
            "feature_b": rng.normal(size=80),
        }
    )

    labels = (
        features["feature_a"] + 0.75 * features["feature_b"] > 0
    ).astype(int)

    model = LogisticRegression(random_state=2026, max_iter=1000)
    model.fit(features, labels)

    predictions = model.predict(features)

    dataset = features.copy()
    dataset[CLASSIFICATION_TARGET] = labels

    metrics = {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(
            precision_score(labels, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(labels, predictions, zero_division=0)
        ),
        "f1": float(
            f1_score(labels, predictions, zero_division=0)
        ),
    }

    joblib.dump(model, CLASSIFICATION_DIR / "model.joblib")
    dataset.to_csv(CLASSIFICATION_DIR / "data.csv", index=False)
    _write_json(
        CLASSIFICATION_DIR / "expected_metrics.json",
        metrics,
    )


def generate_regression_fixture() -> None:
    """Generate a deterministic regression reference fixture."""
    rng = np.random.default_rng(2027)

    features = pd.DataFrame(
        {
            "feature_x": rng.normal(size=80),
            "feature_y": rng.normal(size=80),
        }
    )

    noise = rng.normal(loc=0.0, scale=0.35, size=80)
    targets = (
        3.5 * features["feature_x"]
        - 2.25 * features["feature_y"]
        + 4.0
        + noise
    )

    model = LinearRegression()
    model.fit(features, targets)

    predictions = model.predict(features)

    mse = float(mean_squared_error(targets, predictions))

    metrics = {
        "mae": float(mean_absolute_error(targets, predictions)),
        "mse": mse,
        "r2": float(r2_score(targets, predictions)),
        "rmse": float(np.sqrt(mse)),
    }

    dataset = features.copy()
    dataset[REGRESSION_TARGET] = targets

    joblib.dump(model, REGRESSION_DIR / "model.joblib")
    dataset.to_csv(REGRESSION_DIR / "data.csv", index=False)
    _write_json(
        REGRESSION_DIR / "expected_metrics.json",
        metrics,
    )


def generate_negative_fixtures() -> None:
    """Generate reusable invalid and incompatible input fixtures."""
    (NEGATIVE_DIR / "unsupported.txt").write_text(
        "This file intentionally uses an unsupported extension.\n",
        encoding="utf-8",
    )

    (NEGATIVE_DIR / "malformed.csv").write_text(
        'feature_a,feature_b,label\n1.0,"unterminated,1\n',
        encoding="utf-8",
    )

    (NEGATIVE_DIR / "malformed_model.joblib").write_bytes(
        b"this is intentionally not a valid joblib model\n"
    )

    incompatible = pd.DataFrame(
        {
            "wrong_feature_1": [1.0, 2.0, 3.0],
            "wrong_feature_2": [4.0, 5.0, 6.0],
            CLASSIFICATION_TARGET: [0, 1, 0],
        }
    )
    incompatible.to_csv(
        NEGATIVE_DIR / "incompatible.csv",
        index=False,
    )


def write_file_with_exact_size(path: Path, size_bytes: int) -> Path:
    """Create a file containing exactly ``size_bytes`` bytes.

    This helper supports boundary testing for TC-03 and TC-04, including
    files exactly at the configured upload limit and one byte over it.
    """
    if size_bytes < 0:
        raise ValueError("size_bytes must be non-negative")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size_bytes)
    return path


def generate_all() -> None:
    """Generate the complete EN-02 reference fixture set."""
    _prepare_directories()
    generate_classification_fixture()
    generate_regression_fixture()
    generate_negative_fixtures()


if __name__ == "__main__":
    generate_all()
    print(f"Generated EN-02 fixtures in: {FIXTURES_DIR}")