import io
import pickle
import types
import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import AppError, ErrorCode
from app.main import create_app
from app.results import InMemoryEvaluationStore, ResultService, Status
from app.validation.service import _enforce_file_size
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


@pytest.mark.parametrize("invalid_task", ["clustering", "forecasting", "dimensionality_reduction"])
def test_invalid_task_type_is_rejected(client, store, settings, tmp_path, invalid_task):
    """TC-06: unsupported task types are rejected with 422 INVALID_TASK_TYPE."""
    model, data = write_classification_fixture(tmp_path)
    response = post(client, model, data, task_type=invalid_task)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TASK_TYPE"
    assert store.added == 0
    assert stored_files(settings) == []


def test_target_column_not_in_dataset_is_rejected(client, store, settings, tmp_path):
    """TC-05: submitting a target column not in the CSV header returns 422 INVALID_TARGET_COLUMN."""
    model, data = write_classification_fixture(tmp_path)
    response = post(client, model, data, target_column="nonexistent_target")
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_TARGET_COLUMN"
    assert "nonexistent_target" in error["message"]
    assert store.added == 0
    assert stored_files(settings) == []


def test_valid_target_column_in_dataset_is_accepted(client, store, settings, tmp_path):
    """TC-05 / FR-07: a target column that exists in the CSV header is accepted."""
    model, data = write_classification_fixture(tmp_path, target="custom_label")
    response = post(client, model, data, target_column="custom_label")
    assert response.status_code == 202
    assert response.json()["status"] == "pending"
    assert store.added == 1


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


def test_enforce_file_size_stops_early_without_reading_entire_file():
    """Verify size checking halts immediately upon exceeding limit and resets stream."""

    class TrackingBytesIO(io.BytesIO):
        def __init__(self, initial_bytes):
            super().__init__(initial_bytes)
            self.total_read = 0

        def read(self, size=-1):
            chunk = super().read(size)
            self.total_read += len(chunk)
            return chunk

    # 1 MB of dummy data, limit is 128 KB
    large_payload = b"X" * (1024 * 1024)
    stream = TrackingBytesIO(large_payload)

    with pytest.raises(AppError) as exc_info:
        _enforce_file_size(stream, max_bytes=128 * 1024, field_name="model")

    assert exc_info.value.code is ErrorCode.FILE_TOO_LARGE
    assert stream.tell() == 0
    assert stream.total_read < len(large_payload)


def test_model_exactly_at_size_limit_is_accepted(store, tmp_path):
    """TC-04: model file exactly at the configured size limit is accepted."""
    model, _ = write_classification_fixture(tmp_path)
    model_bytes = model.read_bytes()
    limit = len(model_bytes)

    small_data = b"a,b,label\n1.0,2.0,1\n"
    assert len(small_data) < limit

    custom_settings = Settings(storage_dir=tmp_path / "uploads", max_upload_bytes=limit)
    custom_app = create_app(custom_settings, ResultService(store))
    custom_client = TestClient(custom_app)

    response = custom_client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model_bytes),
            "dataset": ("data.csv", small_data),
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "pending"


def test_model_one_byte_over_size_limit_is_rejected(store, tmp_path):
    """TC-04: model file one byte over the configured size limit is rejected."""
    model, _ = write_classification_fixture(tmp_path)
    model_bytes = model.read_bytes()
    limit = len(model_bytes)

    small_data = b"a,b,label\n1.0,2.0,1\n"
    assert len(small_data) < limit

    custom_settings = Settings(storage_dir=tmp_path / "uploads", max_upload_bytes=limit)
    custom_app = create_app(custom_settings, ResultService(store))
    custom_client = TestClient(custom_app)

    oversized_bytes = model_bytes + b"X"
    response = custom_client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", oversized_bytes),
            "dataset": ("data.csv", small_data),
        },
    )
    assert response.status_code == 413
    error = response.json()["error"]
    assert error["code"] == "FILE_TOO_LARGE"
    assert "model" in error["message"]
    assert store.added == 0
    assert stored_files(custom_settings) == []


def test_dataset_exactly_at_size_limit_is_accepted(store, tmp_path):
    """TC-04: dataset file exactly at the configured size limit is accepted."""
    model, data = write_classification_fixture(tmp_path)
    dataset_bytes = data.read_bytes()
    limit = len(dataset_bytes)

    custom_settings = Settings(storage_dir=tmp_path / "uploads", max_upload_bytes=limit)
    custom_app = create_app(custom_settings, ResultService(store))
    custom_client = TestClient(custom_app)

    response = custom_client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model.read_bytes()),
            "dataset": ("data.csv", dataset_bytes),
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "pending"


def test_dataset_one_byte_over_size_limit_is_rejected(store, tmp_path):
    """TC-04: dataset file one byte over the configured size limit is rejected."""
    model, data = write_classification_fixture(tmp_path)
    dataset_bytes = data.read_bytes()
    limit = len(dataset_bytes)

    custom_settings = Settings(storage_dir=tmp_path / "uploads", max_upload_bytes=limit)
    custom_app = create_app(custom_settings, ResultService(store))
    custom_client = TestClient(custom_app)

    oversized_bytes = dataset_bytes + b"\n"
    response = custom_client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model.read_bytes()),
            "dataset": ("data.csv", oversized_bytes),
        },
    )
    assert response.status_code == 413
    error = response.json()["error"]
    assert error["code"] == "FILE_TOO_LARGE"
    assert "dataset" in error["message"]
    assert store.added == 0
    assert stored_files(custom_settings) == []


@pytest.mark.parametrize(
    ("dataset_bytes", "reason"),
    [
        (b"", "empty-zero-bytes"),
        (b"   \n  \t\n", "whitespace-only"),
        (b"\xff\xfe\x00\x00not-utf8", "non-utf8-bytes"),
        (b"a,b\n1,\x00\n", "contains-null-byte"),
        (b"a,b,c\n1,2\n3,4,5\n", "ragged-too-few-columns"),
        (b"a,b\n1,2\n3,4,5\n", "ragged-extra-columns"),
    ],
)
def test_malformed_csv_is_rejected(client, store, settings, tmp_path, dataset_bytes, reason):
    """TC-23: malformed, empty, unparseable, or ragged CSV files are rejected with 422 MALFORMED_DATASET."""
    model, _ = write_classification_fixture(tmp_path)
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model.read_bytes()),
            "dataset": ("data.csv", dataset_bytes),
        },
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "MALFORMED_DATASET"
    assert store.added == 0
    assert stored_files(settings) == []


@pytest.mark.parametrize(
    ("model_bytes", "reason"),
    [
        (b"not-a-valid-pickle-file", "corrupted-bytes"),
        (pickle.dumps({"dictionary": 123}), "dict-lacks-predict"),
        (pickle.dumps(12345), "int-lacks-predict"),
        (pickle.dumps(types.SimpleNamespace(predict="not_callable")), "non-callable-predict"),
    ],
)
def test_malformed_model_is_rejected(client, store, settings, tmp_path, model_bytes, reason):
    """TC-14: corrupted models or objects without callable predict are rejected with 422 INVALID_MODEL."""
    _, data = write_classification_fixture(tmp_path)
    response = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", model_bytes),
            "dataset": ("data.csv", data.read_bytes()),
        },
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "INVALID_MODEL"
    assert store.added == 0
    assert stored_files(settings) == []



