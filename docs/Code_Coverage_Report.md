# Code Coverage Report
## Web-Based ML Model Evaluator

| | |
|---|---|
| **Date** | 10 November 2026 |
| **Code** | `main` at commit `a6669ab3`, plus the tests and documents added by the pull request that contains these reports |
| **Environment** | Windows 11, Python 3.13.7, pytest 9.1.1, coverage.py 7.17.2, FastAPI 0.116.2, scikit-learn 1.9.1 |
| **Reproduce** | `cd backend`, `pip install -r requirements-dev.txt`, `python scripts/generate_reports.py` |


**Scope.** These reports cover the backend (`backend/app`). The frontend has no automated tests, so it has no unit-test or coverage figures; it was checked by hand against a running backend (System Validation Report, section 6). Adding frontend tests is listed as a defect (DEF-08).

## 1. Summary

Line coverage is the share of executable statements that ran at least once.

| Run | Statements | Covered | Line coverage |
|---|---|---|---|
| **All tests** (unit and system) | 817 | 801 | **98.0%** |
| Unit tests only | 817 | 766 | 93.8% |

## 2. Line coverage by file

| File | Statements | Covered | Line coverage | Unit tests only | Uncovered lines |
|---|---|---|---|---|---|
| `app/api/auth.py` | 81 | 77 | 95.1% | 95.1% | 97-99, 101 |
| `app/api/docs.py` | 13 | 13 | 100.0% | 100.0% | none |
| `app/api/error_handlers.py` | 79 | 79 | 100.0% | 98.7% | none |
| `app/api/evaluations.py` | 40 | 40 | 100.0% | 82.5% | none |
| `app/config.py` | 28 | 28 | 100.0% | 100.0% | none |
| `app/errors.py` | 28 | 28 | 100.0% | 100.0% | none |
| `app/evaluation/__init__.py` | 2 | 2 | 100.0% | 100.0% | none |
| `app/evaluation/runner.py` | 77 | 77 | 100.0% | 79.2% | none |
| `app/evaluation/worker.py` | 50 | 47 | 94.0% | 94.0% | 32-33, 88 |
| `app/main.py` | 23 | 23 | 100.0% | 100.0% | none |
| `app/metrics/__init__.py` | 2 | 2 | 100.0% | 100.0% | none |
| `app/metrics/service.py` | 21 | 21 | 100.0% | 100.0% | none |
| `app/results/__init__.py` | 3 | 3 | 100.0% | 100.0% | none |
| `app/results/formatting.py` | 10 | 10 | 100.0% | 90.0% | none |
| `app/results/service.py` | 85 | 85 | 100.0% | 100.0% | none |
| `app/security/__init__.py` | 2 | 2 | 100.0% | 100.0% | none |
| `app/security/child_process.py` | 8 | 8 | 100.0% | 100.0% | none |
| `app/storage/__init__.py` | 3 | 3 | 100.0% | 100.0% | none |
| `app/storage/lifecycle.py` | 65 | 65 | 100.0% | 100.0% | none |
| `app/storage/temp_storage.py` | 69 | 61 | 88.4% | 88.4% | 41-42, 49-50, 60, 67, 79-80 |
| `app/validation/model_inspector.py` | 16 | 15 | 93.8% | 93.8% | 38 |
| `app/validation/service.py` | 112 | 112 | 100.0% | 91.1% | none |

The files are in `backend/app`. A browsable, line-by-line version with the uncovered lines highlighted is in [`coverage_html/index.html`](coverage_html/index.html).

## 3. Why some lines are not covered

| File | Lines | Reason |
|---|---|---|
| `app/api/auth.py` | 97-99, 101 | Handlers for header text that cannot be encoded. HTTP headers are decoded as Latin-1, so a request cannot reach them; kept as a safety net. |
| `app/evaluation/worker.py` | 32-33 | POSIX only: applying the memory limit needs the `resource` module, which Windows does not have. Runs in the Linux CI job. |
| `app/evaluation/worker.py` | 88 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |
| `app/storage/temp_storage.py` | 41-42, 49-50 | Ignoring a failed permission change: only happens on file systems that do not support it. |
| `app/storage/temp_storage.py` | 60 | A safety check that a random UUID filename can never trigger. |
| `app/storage/temp_storage.py` | 67 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/storage/temp_storage.py` | 79-80 | A second failure while removing a partly written file (the first failure is tested); not reproducible reliably. |
| `app/validation/model_inspector.py` | 38 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |

Code that only runs inside child processes (the model worker and inspector) is measured through the in-process unit tests (`test_worker.py`, `test_model_inspector.py`); the system tests run it for real but coverage cannot follow into the child, so it is not counted twice. Lines marked *POSIX only* run in the Linux CI job, not on a Windows laptop.

## 4. How to reproduce

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html
```
