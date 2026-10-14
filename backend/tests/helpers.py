"""Small deterministic models and datasets for tests (EN-02 adds the shared reference fixtures)."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression


def write_classification_fixture(directory: Path, target: str = "label") -> tuple[Path, Path]:
    rng = np.random.default_rng(0)
    features = pd.DataFrame({"a": rng.normal(size=60), "b": rng.normal(size=60)})
    labels = (features["a"] + features["b"] > 0).astype(int)
    model = LogisticRegression().fit(features, labels)
    return _save(directory, model, features.assign(**{target: labels}))


def write_regression_fixture(directory: Path, target: str = "price") -> tuple[Path, Path]:
    rng = np.random.default_rng(1)
    features = pd.DataFrame({"x1": rng.normal(size=60), "x2": rng.normal(size=60)})
    values = 3 * features["x1"] - 2 * features["x2"] + 1
    model = LinearRegression().fit(features, values)
    return _save(directory, model, features.assign(**{target: values}))


def _save(directory: Path, model, dataset: pd.DataFrame) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    model_path = directory / "model.joblib"
    dataset_path = directory / "data.csv"
    joblib.dump(model, model_path)
    dataset.to_csv(dataset_path, index=False)
    return model_path, dataset_path
