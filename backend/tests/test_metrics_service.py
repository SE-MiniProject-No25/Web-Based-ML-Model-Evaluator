"""Unit tests for classification and regression Metrics Service behaviour."""

from __future__ import annotations

import json

import joblib
import pandas as pd
import pytest

from app.metrics.service import compute
from tests.generate_fixtures import CLASSIFICATION_DIR, REGRESSION_DIR


def test_binary_classification_metrics():
    """Binary classification uses the positive class."""
    y_true = [0, 0, 1, 1]
    y_pred = [0, 1, 1, 1]

    metrics = compute("classification", y_true, y_pred)

    assert metrics == pytest.approx(
        {
            "accuracy": 0.75,
            "precision": 2 / 3,
            "recall": 1.0,
            "f1": 0.8,
        }
    )


def test_multiclass_classification_uses_macro_average():
    """Multiclass precision, recall, and F1 use macro averaging."""
    y_true = [0, 0, 1, 1, 2, 2]
    y_pred = [0, 1, 1, 1, 2, 0]

    metrics = compute("classification", y_true, y_pred)

    assert metrics == pytest.approx(
        {
            "accuracy": 2 / 3,
            "precision": 13 / 18,
            "recall": 2 / 3,
            "f1": 59 / 90,
        }
    )


def test_binary_metrics_handle_missing_positive_predictions():
    """Undefined positive-class metrics return zero without crashing."""
    y_true = [0, 0, 1, 1]
    y_pred = [0, 0, 0, 0]

    metrics = compute("classification", y_true, y_pred)

    assert metrics == pytest.approx(
        {
            "accuracy": 0.5,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }
    )


def test_classification_metrics_match_en02_reference_fixture():
    """Classification results match the reference values from EN-02."""
    model = joblib.load(CLASSIFICATION_DIR / "model.joblib")
    dataset = pd.read_csv(CLASSIFICATION_DIR / "data.csv")

    y_true = dataset["label"].to_numpy()
    features = dataset.drop(columns=["label"])
    y_pred = model.predict(features)

    actual = compute("classification", y_true, y_pred)

    expected = json.loads(
        (CLASSIFICATION_DIR / "expected_metrics.json").read_text(
            encoding="utf-8"
        )
    )

    assert actual == pytest.approx(expected)


def test_regression_metrics():
    """Regression reports MAE, MSE, RMSE, and R²."""
    y_true = [1.0, 2.0, 3.0, 4.0]
    y_pred = [1.0, 2.0, 2.0, 5.0]

    metrics = compute("regression", y_true, y_pred)

    assert metrics == pytest.approx(
        {
            "mae": 0.5,
            "mse": 0.5,
            "rmse": 0.5**0.5,
            "r2": 0.6,
        }
    )


def test_regression_metrics_match_en02_reference_fixture():
    """Regression results match the reference values established by EN-02."""
    model = joblib.load(REGRESSION_DIR / "model.joblib")
    dataset = pd.read_csv(REGRESSION_DIR / "data.csv")

    y_true = dataset["price"].to_numpy()
    features = dataset.drop(columns=["price"])
    y_pred = model.predict(features)

    actual = compute("regression", y_true, y_pred)

    expected = json.loads(
        (REGRESSION_DIR / "expected_metrics.json").read_text(
            encoding="utf-8"
        )
    )

    assert actual == pytest.approx(expected)


def test_constant_regression_target_does_not_crash():
    """A constant target is handled without returning a non-finite R²."""
    y_true = [5.0, 5.0, 5.0, 5.0]
    y_pred = [4.0, 5.0, 6.0, 5.0]

    metrics = compute("regression", y_true, y_pred)

    assert metrics["mae"] == pytest.approx(0.5)
    assert metrics["mse"] == pytest.approx(0.5)
    assert metrics["rmse"] == pytest.approx(0.5**0.5)
    assert metrics["r2"] == pytest.approx(0.0)


def test_unsupported_task_type_is_rejected():
    """Unsupported task types are rejected explicitly."""
    with pytest.raises(ValueError, match="Unsupported task type"):
        compute("clustering", [0, 1], [0, 1])