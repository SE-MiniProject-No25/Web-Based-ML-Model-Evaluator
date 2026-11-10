# Branch Coverage Report
## Web-Based ML Model Evaluator

| | |
|---|---|
| **Date** | 10 November 2026 |
| **Code** | `main` at commit `8200b89f`, plus the tests and documents added by the pull request that contains these reports |
| **Environment** | Windows 11, Python 3.13.7, pytest 9.1.1, coverage.py 7.17.2, FastAPI 0.116.2, scikit-learn 1.9.1 |
| **Reproduce** | `cd backend`, `pip install -r requirements-dev.txt`, `python scripts/generate_reports.py` |


**Scope.** These reports cover the backend (`backend/app`). The frontend has no automated tests, so it has no unit-test or coverage figures; it was checked by hand against a running backend (System Validation Report, section 6). Adding frontend tests is listed as a defect (DEF-08).

## 1. Summary

A branch is one outcome of a decision (the `if` taken, or not taken; a loop entered, or skipped). Branch coverage is the share of those outcomes that ran at least once.

| Run | Branches | Covered | Branch coverage |
|---|---|---|---|
| **All tests** (unit and system) | 198 | 189 | **95.5%** |
| Unit tests only | 198 | 169 | 85.4% |


Lines and branches combined (the figure coverage.py prints as *Cover*): **97.5%**.

## 2. Branch coverage by file

| File | Branches | Covered | Branch coverage | Unit tests only |
|---|---|---|---|---|
| `app/api/auth.py` | 34 | 32 | 94.1% | 94.1% |
| `app/api/error_handlers.py` | 16 | 16 | 100.0% | 93.8% |
| `app/api/evaluations.py` | 4 | 4 | 100.0% | 25.0% |
| `app/config.py` | 2 | 2 | 100.0% | 100.0% |
| `app/evaluation/runner.py` | 16 | 16 | 100.0% | 56.2% |
| `app/evaluation/worker.py` | 10 | 7 | 70.0% | 70.0% |
| `app/metrics/service.py` | 6 | 6 | 100.0% | 100.0% |
| `app/results/formatting.py` | 4 | 4 | 100.0% | 75.0% |
| `app/results/service.py` | 10 | 10 | 100.0% | 100.0% |
| `app/security/child_process.py` | 4 | 4 | 100.0% | 100.0% |
| `app/storage/lifecycle.py` | 30 | 30 | 100.0% | 100.0% |
| `app/storage/temp_storage.py` | 14 | 11 | 78.6% | 78.6% |
| `app/validation/model_inspector.py` | 6 | 5 | 83.3% | 83.3% |
| `app/validation/service.py` | 42 | 42 | 100.0% | 81.0% |

## 3. Branches never taken

8 decision outcomes were never exercised by any test (lines where a branch is only partly taken). Each was reviewed:

| File | Line | Branches taken | Not taken (goes to line) | Reason |
|---|---|---|---|---|
| `app/api/auth.py` | 63 | 1 of 2 | 59 | A token that is empty after trimming cannot occur: splitting the header on whitespace never leaves one. A dead check kept as a safety net. |
| `app/api/auth.py` | 126 | 1 of 2 | 130 | The request always carries its application, so the fall-through to the environment is only reachable when the middleware runs outside Starlette. |
| `app/evaluation/worker.py` | 32 | 0 of 2 | exit,33 | POSIX only: applying the memory limit needs the `resource` module, which Windows does not have. Runs in the Linux CI job. |
| `app/evaluation/worker.py` | 87 | 1 of 2 | 88 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |
| `app/storage/temp_storage.py` | 59 | 1 of 2 | 60 | A safety check that a random UUID filename can never trigger. |
| `app/storage/temp_storage.py` | 64 | 1 of 2 | 66 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/storage/temp_storage.py` | 66 | 1 of 2 | 67 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/validation/model_inspector.py` | 37 | 1 of 2 | 38 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |

## 4. How to reproduce

```bash
cd backend
pytest --cov=app --cov-branch --cov-report=term-missing
```
The *BrPart* column in that output is the same data as section 3.
