"""Unit tests for the model worker (US-04), called in-process.

The runner starts ``worker.py`` as a child process, which code coverage cannot see. Calling its
``main()`` directly tests every outcome it can report and keeps the coverage figures honest.
"""

import json
import sys

import joblib
import pytest

from app.evaluation import worker
from tests.helpers import write_classification_fixture, write_regression_fixture
from tests.slow_models import CountOnlyModel, ExplodingModel, MemoryErrorModel


def run_worker(monkeypatch, tmp_path, model_path, data_path, target="label", memory_limit="0"):
    """Run worker.main() with the given arguments and return the JSON it wrote."""
    result_path = tmp_path / "result.json"
    argv = ["worker.py", str(model_path), str(data_path), target, str(result_path), memory_limit]
    monkeypatch.setattr(sys, "argv", argv)
    worker.main()
    return json.loads(result_path.read_text(encoding="utf-8"))


def test_a_good_model_reports_the_labels_and_predictions(monkeypatch, tmp_path):
    model, data = write_classification_fixture(tmp_path)

    outcome = run_worker(monkeypatch, tmp_path, model, data)

    assert outcome["ok"] is True
    assert len(outcome["y_true"]) == len(outcome["y_pred"]) == 60
    assert set(outcome["y_pred"]) <= {0, 1}


def test_columns_in_a_different_order_are_reordered_to_match_training(monkeypatch, tmp_path):
    model, data = write_classification_fixture(tmp_path)
    lines = data.read_text().splitlines()
    data.write_text("\n".join(",".join(reversed(line.split(","))) for line in lines) + "\n")  # label,b,a

    assert run_worker(monkeypatch, tmp_path, model, data)["ok"] is True


def test_different_feature_names_are_reported_as_incompatible(monkeypatch, tmp_path):
    model, _ = write_classification_fixture(tmp_path / "c")  # trained on a, b
    _, other = write_regression_fixture(tmp_path / "r", target="label")  # x1, x2

    outcome = run_worker(monkeypatch, tmp_path, model, other)

    assert outcome["code"] == "INCOMPATIBLE_INPUTS"
    assert (outcome["missing"], outcome["extra"]) == (["a", "b"], ["x1", "x2"])


def test_a_model_without_feature_names_is_checked_by_count(monkeypatch, tmp_path):
    _, data = write_classification_fixture(tmp_path)
    model = tmp_path / "counts.joblib"
    joblib.dump(CountOnlyModel(), model)
    three = tmp_path / "three.csv"
    three.write_text("a,b,c,label\n1,2,3,0\n")

    outcome = run_worker(monkeypatch, tmp_path, model, three)

    assert outcome == {"ok": False, "code": "INCOMPATIBLE_INPUTS", "expected_count": 2, "given_count": 3}
    assert run_worker(monkeypatch, tmp_path, model, data)["ok"] is True  # two features: fine


def test_running_out_of_memory_is_reported_as_a_resource_limit(monkeypatch, tmp_path, capsys):
    _, data = write_classification_fixture(tmp_path)
    model = tmp_path / "hog.joblib"
    joblib.dump(MemoryErrorModel(), model)

    outcome = run_worker(monkeypatch, tmp_path, model, data)

    assert outcome == {"ok": False, "code": "RESOURCE_LIMIT_EXCEEDED", "reason": "memory"}
    assert "MemoryError" in capsys.readouterr().err  # the traceback goes to stderr, for the server log


def test_any_other_error_is_reported_generically_with_the_traceback_on_stderr(monkeypatch, tmp_path, capsys):
    _, data = write_classification_fixture(tmp_path)
    model = tmp_path / "boom.joblib"
    joblib.dump(ExplodingModel(), model)

    outcome = run_worker(monkeypatch, tmp_path, model, data)

    assert outcome == {"ok": False, "code": "EVALUATION_FAILED"}  # no message: nothing internal can leak
    assert "secret internal detail" in capsys.readouterr().err


def test_a_missing_target_column_is_a_generic_failure(monkeypatch, tmp_path):
    model, data = write_classification_fixture(tmp_path)

    assert run_worker(monkeypatch, tmp_path, model, data, target="nope") == {
        "ok": False,
        "code": "EVALUATION_FAILED",
    }


def test_a_missing_model_file_is_a_generic_failure(monkeypatch, tmp_path):
    _, data = write_classification_fixture(tmp_path)

    outcome = run_worker(monkeypatch, tmp_path, tmp_path / "absent.joblib", data)

    assert outcome == {"ok": False, "code": "EVALUATION_FAILED"}


def test_a_memory_limit_of_zero_means_no_limit():
    assert worker._limit_memory(0) is None  # must not touch the test process


@pytest.mark.skipif(sys.platform == "win32", reason="memory limits need the POSIX resource module")
def test_a_positive_memory_limit_is_applied_on_posix(monkeypatch):
    import resource

    calls = []
    monkeypatch.setattr(resource, "setrlimit", lambda which, limits: calls.append((which, limits)))

    worker._limit_memory(123456789)

    assert calls == [(resource.RLIMIT_AS, (123456789, 123456789))]
