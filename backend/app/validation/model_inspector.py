"""Isolated child process script for safely inspecting untrusted models.

Security Notice:
Deserializing Python pickle and joblib objects can execute arbitrary bytecode.
This script runs in a separate process to protect the main FastAPI server from
unhandled crashes, C-extension segfaults, memory leaks, and thread hangs.

LIMITATION:
This provides process-level fault isolation, NOT an unprivileged sandbox.
The process runs with the privileges of the executing host user. Stronger
protection against arbitrary code execution requires OS-level containerization
or virtualization (e.g. Docker with no network and dropped capabilities).
"""

import importlib
import io
import sys

import joblib

PRELOADED = (
    "sklearn.linear_model",
    "sklearn.ensemble",
    "sklearn.tree",
    "sklearn.pipeline",
    "sklearn.preprocessing",
    "sklearn.compose",
    "sklearn.impute",
)


def preload() -> None:
    for name in PRELOADED:
        try:
            importlib.import_module(name)
        except ImportError:
            pass


def main() -> None:
    # Tell the parent that imports are complete and this process is ready.
    print("READY", flush=True)

    try:
        data = sys.stdin.buffer.read()
        if not data:
            sys.exit(1)

        model = joblib.load(io.BytesIO(data))
    except Exception:
        sys.exit(1)

    if not callable(getattr(model, "predict", None)):
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    preload()
    main()
