"""Models that misbehave on purpose, for the US-04 failure and limit tests.

Defined in an importable module (not in a test file) so joblib can unpickle them in the child
process, which receives the server's import path through PYTHONPATH.
"""

import os
import sys
import time


class SleepyModel:
    """Takes far longer than any test time limit to predict."""

    def predict(self, X):
        time.sleep(60)
        return [0] * len(X)


class MemoryHogModel:
    """Tries to allocate far more memory than any test limit allows."""

    def predict(self, X):
        block = bytearray(4 * 1024 * 1024 * 1024)
        return [len(block)] * len(X)


class ExplodingModel:
    def predict(self, X):
        raise RuntimeError("secret internal detail at /srv/private/path")


class ChattyModel:
    """Writes to stdout and stderr while predicting; the result must be unaffected."""

    def predict(self, X):
        print("hello from the model")
        print("warning from the model", file=sys.stderr)
        return [1] * len(X)


class CountOnlyModel:
    """Like an old estimator: knows how many features it expects but not their names."""

    n_features_in_ = 2

    def predict(self, X):
        return [0] * len(X)


class EnvProbeModel:
    """Reports whether a server secret is visible inside the child process (1 = visible)."""

    def predict(self, X):
        return [1 if os.environ.get("MLEVAL_TEST_SECRET") else 0] * len(X)
