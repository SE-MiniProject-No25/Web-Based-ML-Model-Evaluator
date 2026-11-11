"""Exploratory debugging pass (TEST-11): unusual inputs through the whole application.

Each test is an input that was tried against the running application. The ones marked DEF-11 to DEF-17
were bugs (a misleading rejection, or a generic "could not be completed" failure); the rest already
behaved and are kept as regression tests. See the defect table in docs/System_Validation_Report.md.
"""

import io
import threading

import httpx
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline

from tests.helpers import write_classification_fixture


def model_bytes(model) -> bytes:
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    return buffer.getvalue()


def features(rows: int = 60, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"a": rng.normal(size=rows), "b": rng.normal(size=rows)})


def classifier(labels) -> tuple[bytes, pd.DataFrame]:
    """A logistic regression trained on columns a and b, and the data with the target column added."""
    data = features()
    target = np.where(data["a"] + data["b"] > 0, labels[1], labels[0])
    return model_bytes(LogisticRegression().fit(data, target)), data.assign(label=target)


def regressor() -> tuple[bytes, pd.DataFrame]:
    data = features(seed=1)
    values = 3 * data["a"] - 2 * data["b"] + 1
    return model_bytes(LinearRegression().fit(data, values)), data.assign(price=values)


def evaluate(client, model: bytes, dataset: bytes | str, task_type: str, target: str, names=None):
    """Submit, and return the submit response and (when accepted) the final status body."""
    if isinstance(dataset, str):
        dataset = dataset.encode("utf-8")
    model_name, dataset_name = names or ("model.joblib", "data.csv")
    response = client.post(
        "/api/evaluations",
        data={"task_type": task_type, "target_column": target},
        files={"model": (model_name, model), "dataset": (dataset_name, dataset)},
    )
    if response.status_code != 202:
        return response, None
    return response, client.get(f"/api/evaluations/{response.json()['evaluation_id']}").json()


def failed_with(body, code: str, *phrases: str) -> None:
    assert body["status"] == "failed", body
    assert body["error"]["code"] == code
    for phrase in phrases:
        assert phrase in body["error"]["message"]


# --- class labels -------------------------------------------------------------------------------------


@pytest.mark.parametrize("labels", [("no", "yes"), ("ham", "spam"), (1, 2), (-1, 1), ("0", "1")])
def test_binary_labels_other_than_0_and_1_are_scored(client, labels):
    """DEF-11: text labels failed because precision, recall and F1 assumed the positive class is 1."""
    model, data = classifier(labels)
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    assert body["status"] == "completed", body
    assert set(body["metrics"]) == {"accuracy", "precision", "recall", "f1"}
    assert body["metrics"]["accuracy"] > 0.9


def test_three_text_classes_are_scored(client):
    data = features()
    target = np.select([data["a"] < -0.5, data["a"] > 0.5], ["low", "high"], "mid")
    model = model_bytes(LogisticRegression().fit(data, target))
    csv = data.assign(label=target).to_csv(index=False)
    _, body = evaluate(client, model, csv, "classification", "label")
    assert body["status"] == "completed", body


# --- the CSV file -------------------------------------------------------------------------------------


def test_a_header_with_spaces_after_the_commas_is_accepted(client):
    """DEF-12: "a, b, label" was rejected because the interface sends the trimmed name "label"."""
    model, data = classifier((0, 1))
    csv = data.to_csv(index=False).replace(",", ", ")
    _, body = evaluate(client, model, csv, "classification", "label")
    assert body["status"] == "completed", body


def test_an_excel_byte_order_mark_before_the_target_column_is_accepted(client):
    """DEF-13: with the target as the first column, the byte-order mark made it "\\ufefflabel"."""
    model, data = classifier((0, 1))
    csv = "﻿" + data[["label", "a", "b"]].to_csv(index=False)
    _, body = evaluate(client, model, csv, "classification", "label")
    assert body["status"] == "completed", body


@pytest.mark.parametrize(("separator", "name"), [(";", "semicolons"), ("\t", "tabs")])
def test_a_csv_with_another_separator_is_rejected_with_a_clear_message(client, separator, name):
    """DEF-14: a semicolon CSV was rejected with "the target column does not exist"."""
    model, data = classifier((0, 1))
    response, _ = evaluate(client, model, data.to_csv(index=False, sep=separator), "classification", "label")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MALFORMED_DATASET"
    assert name in response.json()["error"]["message"]


def test_a_single_column_csv_without_separators_is_not_mistaken_for_one(client):
    model, _ = classifier((0, 1))
    response, body = evaluate(client, model, "label\n0\n1\n", "classification", "label")
    assert response.status_code == 202
    failed_with(body, "INCOMPATIBLE_INPUTS", "Missing from the dataset: a, b")


# --- missing and unexpected values --------------------------------------------------------------------


def test_empty_cells_in_the_target_column_are_named(client):
    """DEF-15: empty target cells ended as the generic failure."""
    model, data = classifier((0, 1))
    data["label"] = data["label"].astype(object)
    data.loc[[3, 7], "label"] = None
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "2 empty value(s)")


def test_empty_cells_in_a_feature_are_named(client):
    """DEF-15: a model that cannot handle empty cells ended as the generic failure."""
    model, data = classifier((0, 1))
    data.loc[5, "b"] = None
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "empty cells in b")


def test_a_pipeline_that_fills_empty_cells_still_works(client):
    data = features()
    target = (data["a"] > 0).astype(int)
    model = model_bytes(make_pipeline(SimpleImputer(), LogisticRegression()).fit(data, target))
    data.loc[5, "b"] = None
    csv = data.assign(label=target).to_csv(index=False)
    _, body = evaluate(client, model, csv, "classification", "label")
    assert body["status"] == "completed", body


def test_text_in_a_numeric_feature_is_named(client):
    model, data = classifier((0, 1))
    data["a"] = data["a"].astype(object)
    data.loc[2, "a"] = "unknown"  # ("n/a" and "NA" are read as empty cells)
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "text where the model expects numbers in a")


# --- the task type does not suit the data or the model ------------------------------------------------


def test_regression_on_a_text_target_says_so(client):
    """DEF-16: ended as the generic failure."""
    model, data = classifier(("no", "yes"))
    _, body = evaluate(client, model, data.to_csv(index=False), "regression", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "numeric target", "contains text")


def test_a_regression_model_evaluated_as_classification_says_so(client):
    """DEF-16: ended as the generic failure."""
    model, data = regressor()
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "price")
    failed_with(body, "INCOMPATIBLE_INPUTS", "looks like a regression model")


def test_a_classifier_with_text_labels_evaluated_as_regression_says_so(client):
    model, data = classifier(("no", "yes"))
    data["label"] = np.where(data["label"] == "yes", 1, 0)
    _, body = evaluate(client, model, data.to_csv(index=False), "regression", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "predicts labels")


def test_text_predictions_against_a_numeric_target_say_so(client):
    model, data = classifier(("no", "yes"))
    data["label"] = np.where(data["label"] == "yes", 1, 0)
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "predicts text", "contains numbers")


def test_classification_on_a_continuous_target_says_so(client):
    model, data = classifier((0, 1))
    data["label"] = data["a"] * 1.5
    _, body = evaluate(client, model, data.to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "continuous values, not classes")


# --- size and shape -----------------------------------------------------------------------------------


@pytest.mark.parametrize(("task_type", "target"), [("classification", "label"), ("regression", "price")])
def test_a_dataset_with_one_row_is_scored(client, task_type, target):
    model, data = classifier((0, 1)) if task_type == "classification" else regressor()
    _, body = evaluate(client, model, data.head(1).to_csv(index=False), task_type, target)
    assert body["status"] == "completed", body


def test_a_header_only_dataset_says_there_are_no_rows(client):
    model, data = classifier((0, 1))
    _, body = evaluate(client, model, data.head(0).to_csv(index=False), "classification", "label")
    failed_with(body, "INCOMPATIBLE_INPUTS", "no rows")


def test_very_wide_data_is_scored(client):
    rng = np.random.default_rng(2)
    data = pd.DataFrame(rng.normal(size=(80, 500)), columns=[f"f{i}" for i in range(500)])
    target = (data["f0"] > 0).astype(int)
    model = model_bytes(LogisticRegression(max_iter=500).fit(data, target))
    csv = data.assign(label=target).to_csv(index=False)
    _, body = evaluate(client, model, csv, "classification", "label")
    assert body["status"] == "completed", body


# --- repeated and simultaneous submissions, filenames -------------------------------------------------


def test_the_same_submission_repeated_gives_new_ids_and_the_same_result(client):
    model, data = classifier((0, 1))
    csv = data.to_csv(index=False)
    bodies = [evaluate(client, model, csv, "classification", "label")[1] for _ in range(3)]
    assert len({body["evaluation_id"] for body in bodies}) == 3
    assert all(body["metrics"] == bodies[0]["metrics"] for body in bodies)


@pytest.mark.parametrize(
    "names",
    [
        ("my model (final) v2.joblib", "data set 2026.csv"),
        ("模型.joblib", "données.csv"),
        ("..\\..\\model.joblib", "../../etc/data.csv"),
        ("model.JOBLIB", "DATA.CSV"),
    ],
)
def test_unusual_filenames_are_accepted_and_kept_only_as_labels(client, settings, names):
    model, data = classifier((0, 1))
    response, body = evaluate(client, model, data.to_csv(index=False), "classification", "label", names)
    assert response.status_code == 202, response.text
    assert body["status"] == "completed"
    stored = [p.name for p in settings.storage_dir.rglob("*") if p.is_file()]
    assert not any(name in names[0] or name in names[1] for name in stored)


def test_two_evaluations_at_the_same_time_on_a_real_server(server_url, tmp_path):
    model_path, data_path = write_classification_fixture(tmp_path)
    results = {}

    def submit(index):
        with open(model_path, "rb") as model, open(data_path, "rb") as data:
            response = httpx.post(
                f"{server_url}/api/evaluations",
                data={"task_type": "classification", "target_column": "label"},
                files={"model": ("m.joblib", model), "dataset": ("d.csv", data)},
                timeout=30,
            )
        results[index] = response

    threads = [threading.Thread(target=submit, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    ids = [results[i].json()["evaluation_id"] for i in range(2)]
    assert len(set(ids)) == 2
    for evaluation_id in ids:
        for _ in range(150):
            body = httpx.get(f"{server_url}/api/evaluations/{evaluation_id}", timeout=5).json()
            if body["status"] in ("completed", "failed"):
                break
            threading.Event().wait(0.2)
        assert body["status"] == "completed", body
