"""Tests for the shared EN-02 reference fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from tests.generate_fixtures import (
    CLASSIFICATION_DIR,
    NEGATIVE_DIR,
    REGRESSION_DIR,
    generate_all,
    write_file_with_exact_size,
)


@pytest.fixture(scope="module", autouse=True)
def ensure_reference_fixtures() -> None:
    """Ensure the shared fixtures exist before validating them."""
    generate_all()


def _read_expected(path: Path) -> dict[str, float]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_classification_reference_files_exist():
    assert (CLASSIFICATION_DIR / "model.joblib").is_file()
    assert (CLASSIFICATION_DIR / "data.csv").is_file()
    assert (CLASSIFICATION_DIR / "expected_metrics.json").is_file()


def test_classification_reference_metrics_match():
    model = joblib.load(CLASSIFICATION_DIR / "model.joblib")
    dataset = pd.read_csv(CLASSIFICATION_DIR / "data.csv")

    y_true = dataset["label"].to_numpy()
    features = dataset.drop(columns=["label"])
    y_pred = model.predict(features)

    actual = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(
            precision_score(y_true, y_pred, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, zero_division=0)
        ),
        "f1": float(
            f1_score(y_true, y_pred, zero_division=0)
        ),
    }

    expected = _read_expected(
        CLASSIFICATION_DIR / "expected_metrics.json"
    )

    assert actual == pytest.approx(expected)


def test_regression_reference_files_exist():
    assert (REGRESSION_DIR / "model.joblib").is_file()
    assert (REGRESSION_DIR / "data.csv").is_file()
    assert (REGRESSION_DIR / "expected_metrics.json").is_file()


def test_regression_reference_metrics_match():
    model = joblib.load(REGRESSION_DIR / "model.joblib")
    dataset = pd.read_csv(REGRESSION_DIR / "data.csv")

    y_true = dataset["price"].to_numpy()
    features = dataset.drop(columns=["price"])
    y_pred = model.predict(features)

    mse = float(mean_squared_error(y_true, y_pred))

    actual = {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "mse": mse,
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(np.sqrt(mse)),
    }

    expected = _read_expected(
        REGRESSION_DIR / "expected_metrics.json"
    )

    assert actual == pytest.approx(expected)


def test_negative_reference_files_exist():
    expected_files = {
        "unsupported.txt",
        "malformed.csv",
        "malformed_model.joblib",
        "incompatible.csv",
    }

    actual_files = {
        path.name
        for path in NEGATIVE_DIR.iterdir()
        if path.is_file()
    }

    assert expected_files.issubset(actual_files)


def test_malformed_model_cannot_be_loaded():
    with pytest.raises((ValueError, EOFError, KeyError, IndexError)):
        joblib.load(NEGATIVE_DIR / "malformed_model.joblib")


def test_incompatible_dataset_has_wrong_features():
    dataset = pd.read_csv(NEGATIVE_DIR / "incompatible.csv")

    assert "label" in dataset.columns
    assert {"wrong_feature_1", "wrong_feature_2"}.issubset(
        dataset.columns
    )
    assert "feature_a" not in dataset.columns
    assert "feature_b" not in dataset.columns


def test_size_limit_helper_creates_exact_size(tmp_path):
    limit = 4096

    exact = write_file_with_exact_size(
        tmp_path / "exact-limit.bin",
        limit,
    )
    over = write_file_with_exact_size(
        tmp_path / "over-limit.bin",
        limit + 1,
    )

    assert exact.stat().st_size == limit
    assert over.stat().st_size == limit + 1


def test_size_limit_helper_rejects_negative_size(tmp_path):
    with pytest.raises(ValueError):
        write_file_with_exact_size(
            tmp_path / "invalid.bin",
            -1,
        )


def test_path_traversal_filename_case_is_representable():
    """TC-13 uses this submitted filename; it is not a physical fixture path."""
    malicious_filename = "../../evil.csv"

    assert ".." in Path(malicious_filename).parts
    assert Path(malicious_filename).name == "evil.csv"


def test_fixture_generation_is_reproducible():
    generate_all()

    first_classification_data = (
        CLASSIFICATION_DIR / "data.csv"
    ).read_bytes()
    first_classification_metrics = (
        CLASSIFICATION_DIR / "expected_metrics.json"
    ).read_bytes()
    first_regression_data = (
        REGRESSION_DIR / "data.csv"
    ).read_bytes()
    first_regression_metrics = (
        REGRESSION_DIR / "expected_metrics.json"
    ).read_bytes()

    generate_all()

    assert (
        CLASSIFICATION_DIR / "data.csv"
    ).read_bytes() == first_classification_data

    assert (
        CLASSIFICATION_DIR / "expected_metrics.json"
    ).read_bytes() == first_classification_metrics

    assert (
        REGRESSION_DIR / "data.csv"
    ).read_bytes() == first_regression_data

    assert (
        REGRESSION_DIR / "expected_metrics.json"
    ).read_bytes() == first_regression_metrics