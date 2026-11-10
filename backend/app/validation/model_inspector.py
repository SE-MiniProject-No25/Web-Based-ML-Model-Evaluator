"""Isolated child process script for safely inspecting untrusted models (US-07).

Security Notice:
Deserializing Python pickle and joblib objects can execute arbitrary bytecode.
This script is executed in an isolated child process to protect the main FastAPI
server from unhandled crashes, C-extension segfaults, memory leaks, and thread
hangs.

LIMITATION:
This mechanism provides process-level fault isolation, NOT an unprivileged,
sandboxed container. It runs with the privileges of the executing host user.
Complete defense against arbitrary code execution requires OS-level containerization
or virtualization (e.g., Docker with no network and dropped capabilities).
"""

import importlib
import io
import sys

import joblib

# Imported before the model arrives, so that a spare inspector started ahead of time (see
# ``InspectorPool`` in service.py) has already paid for them. Unpickling imports whatever else it needs.
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
