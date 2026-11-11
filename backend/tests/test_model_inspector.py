"""Unit tests for the model inspector run during validation (US-07), called in-process.

The validation service starts ``model_inspector.py`` as a child process; calling ``main()`` here tests each
exit status it can return (0 = usable model, 1 = cannot be loaded, 2 = no callable predict).
"""

import io
import sys
from types import SimpleNamespace

import joblib
import pytest

from app.validation import model_inspector
from tests.helpers import write_classification_fixture
from tests.slow_models import NotCallablePredictModel


def inspect(monkeypatch, data: bytes) -> int:
    """Run the inspector with ``data`` on stdin and return its exit status."""
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data)))
    with pytest.raises(SystemExit) as stopped:
        model_inspector.main()
    return stopped.value.code


def dumped(obj, tmp_path) -> bytes:
    path = tmp_path / "obj.joblib"
    joblib.dump(obj, path)
    return path.read_bytes()


def test_a_usable_model_exits_zero(monkeypatch, tmp_path):
    model, _ = write_classification_fixture(tmp_path)
    assert inspect(monkeypatch, model.read_bytes()) == 0


def test_an_empty_upload_exits_one(monkeypatch):
    assert inspect(monkeypatch, b"") == 1


def test_bytes_that_are_not_a_model_file_exit_one(monkeypatch):
    assert inspect(monkeypatch, b"this is not a pickle") == 1


def test_an_object_without_predict_exits_two(monkeypatch, tmp_path):
    assert inspect(monkeypatch, dumped({"not": "a model"}, tmp_path)) == 2


def test_a_predict_that_is_not_callable_exits_two(monkeypatch, tmp_path):
    assert inspect(monkeypatch, dumped(NotCallablePredictModel(), tmp_path)) == 2


def test_preloading_imports_the_common_estimators_and_skips_missing_ones(monkeypatch):
    monkeypatch.setattr(model_inspector, "PRELOADED", ("sklearn.linear_model", "no_such_module_here"))
    model_inspector.preload()

    assert "sklearn.linear_model" in sys.modules
