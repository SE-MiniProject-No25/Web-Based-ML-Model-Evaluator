"""Isolated child process that runs a model on a dataset (US-04, SEC-04).

``joblib.load`` executes code contained in the model file, so the runner never loads a model in
the server process. It starts this script instead, with a sanitized environment, a wall-clock
timeout and (where the OS supports it) a memory limit.

Usage: ``worker.py MODEL_PATH DATASET_PATH TARGET_COLUMN RESULT_PATH MEMORY_LIMIT_BYTES``

The outcome is written as JSON to RESULT_PATH rather than stdout, because model code is free to
print. Tracebacks go to stderr, which the runner logs server-side only. This file imports nothing
from ``app`` so it can run standalone.

LIMITATION: this is process isolation, not an unprivileged container sandbox.
"""

import json
import sys
import traceback


def _write(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as out:
        json.dump(payload, out)


def _limit_memory(limit_bytes: int) -> None:
    """Cap the address space on POSIX systems; a no-op where the ``resource`` module is missing."""
    try:
        import resource
    except ImportError:
        return
    if limit_bytes > 0:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))


def main() -> None:
    model_path, dataset_path, target, result_path, memory_limit = sys.argv[1:6]
    try:
        # Import the libraries first so the memory limit only covers the model and the data.
        import joblib
        import numpy as np
        import pandas as pd

        _limit_memory(int(memory_limit))

        model = joblib.load(model_path)
        dataset = pd.read_csv(dataset_path)
        y_true = dataset[target].to_numpy()
        features = dataset.drop(columns=[target])
        features.columns = [str(c) for c in features.columns]

        expected = getattr(model, "feature_names_in_", None)
        if expected is not None:
            expected = [str(c) for c in expected]
            given = list(features.columns)
            missing = [c for c in expected if c not in given]
            extra = [c for c in given if c not in expected]
            if missing or extra:
                report = {"ok": False, "code": "INCOMPATIBLE_INPUTS", "missing": missing, "extra": extra}
                _write(result_path, report)
                return
            features = features[expected]  # same column order as at training time
        else:
            expected_count = getattr(model, "n_features_in_", None)
            if expected_count is not None and expected_count != features.shape[1]:
                _write(
                    result_path,
                    {
                        "ok": False,
                        "code": "INCOMPATIBLE_INPUTS",
                        "expected_count": int(expected_count),
                        "given_count": int(features.shape[1]),
                    },
                )
                return

        y_pred = np.asarray(model.predict(features))
        _write(result_path, {"ok": True, "y_true": y_true.tolist(), "y_pred": y_pred.tolist()})
    except MemoryError:
        traceback.print_exc()
        _write(result_path, {"ok": False, "code": "RESOURCE_LIMIT_EXCEEDED", "reason": "memory"})
    except Exception:
        traceback.print_exc()
        _write(result_path, {"ok": False, "code": "EVALUATION_FAILED"})


if __name__ == "__main__":
    main()
