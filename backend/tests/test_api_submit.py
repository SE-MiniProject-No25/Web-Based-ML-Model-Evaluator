import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.results import InMemoryEvaluationStore, ResultService, Status
from tests.helpers import write_classification_fixture, write_regression_fixture


class CountingStore(InMemoryEvaluationStore):
    def __init__(self):
        super().__init__()
        self.added = 0

    def add(self, evaluation):
        self.added += 1
        super().add(evaluation)


@pytest.fixture
def store():
    return CountingStore()


@pytest.fixture
def app(settings, store):
    return create_app(settings, ResultService(store))


@pytest.fixture
def client(app):
    return TestClient(app)


def post(client, model_path, dataset_path, **form):
    fields = {"task_type": "classification", "target_column": "label", **form}
    fields = {k: v for k, v in fields.items() if v is not None}
    files = {}
    if model_path is not None:
        files["model"] = (model_path.name, model_path.read_bytes())
    if dataset_path is not None:
        files["dataset"] = (dataset_path.name, dataset_path.read_bytes())
    return client.post("/api/evaluations", data=fields, files=files)


def stored_files(settings):
    return list(settings.storage_dir.iterdir())


def test_valid_classification_submission_is_accepted_with_an_id(client, app, tmp_path):
    """TC-01 / TC-02: a supported model and a valid CSV are accepted."""
    model, data = write_classification_fixture(tmp_path)
    response = post(client, model, data)

    assert response.status_code == 202
    body = response.json()
    assert set(body) == {"evaluation_id", "status"}
    assert body["status"] == "pending"
    assert uuid.UUID(body["evaluation_id"]).version == 4
    assert app.state.results.get(body["evaluation_id"]).task_type == "classification"


def test_the_evaluation_runs_in_the_background_after_the_202(client, app, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    evaluation_id = post(client, model, data).json()["evaluation_id"]
    # The test client waits for background tasks, so the run has finished by now.
    finished = app.state.results.get(evaluation_id)
    assert finished.status is Status.COMPLETED
    assert finished.metrics is not None


def test_valid_regression_submission_is_accepted(client, tmp_path):
    model, data = write_regression_fixture(tmp_path)
    response = post(client, model, data, task_type="regression", target_column="price")
    assert response.status_code == 202


def test_each_submission_gets_a_different_id(client, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    ids = {post(client, model, data).json()["evaluation_id"] for _ in range(5)}
    assert len(ids) == 5


@pytest.mark.parametrize("missing", ["model", "dataset", "task_type", "target_column"])
def test_missing_field_is_rejected_and_creates_nothing(client, store, settings, tmp_path, missing):
    model, data = write_classification_fixture(tmp_path)
    response = post(
        client,
        None if missing == "model" else model,
        None if missing == "dataset" else data,
        task_type=None if missing == "task_type" else "classification",
        target_column=None if missing == "target_column" else "label",
    )
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "MISSING_REQUIRED_FIELD"
    assert missing in error["message"]
    assert store.added == 0
    assert stored_files(settings) == []


def test_unsupported_file_type_is_rejected_and_creates_nothing(client, store, settings, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    exe = tmp_path / "setup.exe"
    exe.write_bytes(b"MZ")
    for bad_model, bad_data in ((exe, data), (model, exe)):
        response = post(client, bad_model, bad_data)
        assert response.status_code == 415
        assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert store.added == 0
    assert stored_files(settings) == []


def test_invalid_task_type_is_rejected(client, store, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    response = post(client, model, data, task_type="clustering")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TASK_TYPE"
    assert store.added == 0


def test_error_responses_use_the_standard_format_without_internal_details(client, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    body = post(client, model, data, task_type="nope").json()
    assert list(body) == ["error"]
    assert set(body["error"]) == {"code", "message"}
    assert str(tmp_path) not in body["error"]["message"]


def test_client_filenames_never_reach_the_filesystem(client, app, settings, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": (r"..\..\model.joblib", model.read_bytes()),
            "dataset": ("../../evil.csv", data.read_bytes()),
        },
    )
    assert response.status_code == 202
    names = {p.name for p in stored_files(settings)}
    assert len(names) == 2
    assert all(len(n.split(".")[0]) == 32 for n in names)  # uuid4 hex names
    record = app.state.results.get(response.json()["evaluation_id"])
    assert (record.model_filename, record.dataset_filename) == ("model.joblib", "evil.csv")
    assert not (tmp_path.parent / "evil.csv").exists()
