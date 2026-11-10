"""Environment for child processes that load untrusted model files (SEC-03, SEC-04).

The child gets a minimal environment, so secrets held in the server's environment
variables (API keys, tokens) are not visible to code inside an uploaded model. It
does get the server's own ``sys.path``: a stripped environment otherwise hides how
this interpreter finds its packages (for example pip --user installs on Windows are
located through APPDATA), and the child would fail to import joblib.
"""

import os
import sys


def sanitized_env() -> dict[str, str]:
    env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": os.pathsep.join(p for p in sys.path if p),
        # One thread per numeric library: predictable memory use and no oversubscription.
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
    for var in ("TEMP", "TMP", "WINDIR", "USERPROFILE"):
        if var in os.environ:
            env[var] = os.environ[var]
    return env
