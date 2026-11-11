# Code Coverage Report
## Web-Based ML Model Evaluator

| | |
|---|---|
| **Date** | 11 November 2026 |
| **Code** | `main` at commit `253d236b`, plus the tests and documents added by the pull request that contains these reports |
| **Environment** | Windows 11, Python 3.13.7, pytest 9.1.1, coverage.py 7.17.2, FastAPI 0.116.2, scikit-learn 1.9.1 |
| **Reproduce** | `cd backend`, `pip install -r requirements-dev.txt`, `python scripts/generate_reports.py` |


**Scope.** The figures below are for the backend (`backend/app`, pytest and coverage.py). The frontend (`frontend/src`) has its own tests (Vitest and React Testing Library, `npm run coverage`): **28 of 28 passed**, **88.3% of lines** and **75.8% of branches** covered:

| Frontend file | Lines | Branches |
|---|---|---|
| `frontend/src/App.jsx` | 87.0% | 71.3% |
| `frontend/src/api.js` | 91.1% | 87.1% |
| `frontend/src/metrics.js` | 100.0% | 100.0% |

## 1. Summary

Line coverage is the share of executable statements that ran at least once.

| Run | Statements | Covered | Line coverage |
|---|---|---|---|
| **All tests** (unit and system) | 1031 | 1006 | **97.6%** |
| Unit tests only | 1031 | 947 | 91.9% |

## 2. Line coverage by file

| File | Statements | Covered | Line coverage | Unit tests only | Uncovered lines |
|---|---|---|---|---|---|
| `app/api/auth.py` | 81 | 77 | 95.1% | 95.1% | 97-99, 101 |
| `app/api/docs.py` | 13 | 13 | 100.0% | 100.0% | none |
| `app/api/error_handlers.py` | 79 | 79 | 100.0% | 98.7% | none |
| `app/api/evaluations.py` | 41 | 41 | 100.0% | 82.9% | none |
| `app/api/retention.py` | 26 | 26 | 100.0% | 100.0% | none |
| `app/config.py` | 30 | 30 | 100.0% | 100.0% | none |
| `app/errors.py` | 28 | 28 | 100.0% | 100.0% | none |
| `app/evaluation/__init__.py` | 2 | 2 | 100.0% | 100.0% | none |
| `app/evaluation/runner.py` | 118 | 118 | 100.0% | 72.0% | none |
| `app/evaluation/worker.py` | 76 | 73 | 96.1% | 96.1% | 32-33, 129 |
| `app/main.py` | 27 | 27 | 100.0% | 100.0% | none |
| `app/metrics/__init__.py` | 2 | 2 | 100.0% | 100.0% | none |
| `app/metrics/service.py` | 31 | 29 | 93.5% | 87.1% | 76-77 |
| `app/results/__init__.py` | 3 | 3 | 100.0% | 100.0% | none |
| `app/results/formatting.py` | 10 | 10 | 100.0% | 90.0% | none |
| `app/results/service.py` | 90 | 90 | 100.0% | 100.0% | none |
| `app/security/__init__.py` | 3 | 3 | 100.0% | 100.0% | none |
| `app/security/child_process.py` | 8 | 8 | 100.0% | 100.0% | none |
| `app/security/memory_limit.py` | 46 | 40 | 87.0% | 84.8% | 83-84, 93-96 |
| `app/storage/__init__.py` | 3 | 3 | 100.0% | 100.0% | none |
| `app/storage/lifecycle.py` | 65 | 65 | 100.0% | 100.0% | none |
| `app/storage/temp_storage.py` | 69 | 61 | 88.4% | 88.4% | 41-42, 49-50, 60, 67, 79-80 |
| `app/validation/model_inspector.py` | 25 | 23 | 92.0% | 92.0% | 59-60 |
| `app/validation/service.py` | 155 | 155 | 100.0% | 91.0% | none |

The files are in `backend/app`. A browsable, line-by-line version with the uncovered lines highlighted is in [`coverage_html/index.html`](coverage_html/index.html).

## 3. Why some lines are not covered

| File | Lines | Reason |
|---|---|---|
| `app/api/auth.py` | 97-99, 101 | Handlers for header text that cannot be encoded. HTTP headers are decoded as Latin-1, so a request cannot reach them; kept as a safety net. |
| `app/evaluation/worker.py` | 32-33 | POSIX only: applying the memory limit needs the `resource` module, which Windows does not have. Runs in the Linux CI job. |
| `app/evaluation/worker.py` | 129 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |
| `app/metrics/service.py` | 76-77 | Labels of different types (numbers and text together). The runner compares such labels as text, or rejects them, before scoring, so this fallback is only a safety net. |
| `app/security/memory_limit.py` | 83-84 | Windows refusing to create a job object: an operating-system failure that cannot be caused from a test. The evaluation then runs with its time limit only, and a warning is logged. |
| `app/security/memory_limit.py` | 93-96 | Windows refusing to apply the limit to the process: an operating-system failure that cannot be caused from a test. Same fallback as above. |
| `app/storage/temp_storage.py` | 41-42, 49-50 | Ignoring a failed permission change: only happens on file systems that do not support it. |
| `app/storage/temp_storage.py` | 60 | A safety check that a random UUID filename can never trigger. |
| `app/storage/temp_storage.py` | 67 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/storage/temp_storage.py` | 79-80 | A second failure while removing a partly written file (the first failure is tested); not reproducible reliably. |
| `app/validation/model_inspector.py` | 59-60 | The `if __name__ == "__main__"` entry point. The system tests (and the spare inspectors) run it as a child process, which coverage does not follow. |

Code that only runs inside child processes (the model worker and inspector) is measured through the in-process unit tests (`test_worker.py`, `test_model_inspector.py`); the system tests run it for real but coverage cannot follow into the child, so it is not counted twice. Lines marked *POSIX only* run in the Linux CI job, not on a Windows laptop.

## 4. How to reproduce

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html
```
