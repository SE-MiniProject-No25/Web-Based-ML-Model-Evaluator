# Branch Coverage Report
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

A branch is one outcome of a decision (the `if` taken, or not taken; a loop entered, or skipped). Branch coverage is the share of those outcomes that ran at least once.

| Run | Branches | Covered | Branch coverage |
|---|---|---|---|
| **All tests** (unit and system) | 256 | 244 | **95.3%** |
| Unit tests only | 256 | 205 | 80.1% |


Lines and branches combined (the figure coverage.py prints as *Cover*): **97.1%**.

## 2. Branch coverage by file

| File | Branches | Covered | Branch coverage | Unit tests only |
|---|---|---|---|---|
| `app/api/auth.py` | 34 | 32 | 94.1% | 94.1% |
| `app/api/error_handlers.py` | 16 | 16 | 100.0% | 93.8% |
| `app/api/evaluations.py` | 4 | 4 | 100.0% | 25.0% |
| `app/api/retention.py` | 2 | 2 | 100.0% | 100.0% |
| `app/config.py` | 2 | 2 | 100.0% | 100.0% |
| `app/evaluation/runner.py` | 38 | 37 | 97.4% | 44.7% |
| `app/evaluation/worker.py` | 20 | 17 | 85.0% | 85.0% |
| `app/metrics/service.py` | 10 | 10 | 100.0% | 90.0% |
| `app/results/formatting.py` | 4 | 4 | 100.0% | 75.0% |
| `app/results/service.py` | 10 | 10 | 100.0% | 100.0% |
| `app/security/child_process.py` | 4 | 4 | 100.0% | 100.0% |
| `app/security/memory_limit.py` | 8 | 6 | 75.0% | 50.0% |
| `app/storage/lifecycle.py` | 30 | 30 | 100.0% | 100.0% |
| `app/storage/temp_storage.py` | 14 | 11 | 78.6% | 78.6% |
| `app/validation/model_inspector.py` | 8 | 7 | 87.5% | 87.5% |
| `app/validation/service.py` | 52 | 52 | 100.0% | 78.8% |

## 3. Branches never taken

11 decision outcomes were never exercised by any test (lines where a branch is only partly taken). Each was reviewed:

| File | Line | Branches taken | Not taken (goes to line) | Reason |
|---|---|---|---|---|
| `app/api/auth.py` | 63 | 1 of 2 | 59 | A token that is empty after trimming cannot occur: splitting the header on whitespace never leaves one. A dead check kept as a safety net. |
| `app/api/auth.py` | 126 | 1 of 2 | 130 | The request always carries its application, so the fall-through to the environment is only reachable when the middleware runs outside Starlette. |
| `app/evaluation/runner.py` | 120 | 1 of 2 | 123 | The memory limit is always applied on Windows (where these reports were generated), so the branch for no job object runs only on Linux and macOS, in the Linux CI job. |
| `app/evaluation/worker.py` | 32 | 0 of 2 | exit,33 | POSIX only: applying the memory limit needs the `resource` module, which Windows does not have. Runs in the Linux CI job. |
| `app/evaluation/worker.py` | 128 | 1 of 2 | 129 | The `if __name__ == "__main__"` entry point. The system tests run it as a child process, which coverage does not follow. |
| `app/security/memory_limit.py` | 82 | 1 of 2 | 83 | Windows refusing to create a job object: an operating-system failure that cannot be caused from a test. The evaluation then runs with its time limit only, and a warning is logged. |
| `app/security/memory_limit.py` | 92 | 1 of 2 | 93 | Windows refusing to apply the limit to the process: an operating-system failure that cannot be caused from a test. Same fallback as above. |
| `app/storage/temp_storage.py` | 59 | 1 of 2 | 60 | A safety check that a random UUID filename can never trigger. |
| `app/storage/temp_storage.py` | 64 | 1 of 2 | 66 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/storage/temp_storage.py` | 66 | 1 of 2 | 67 | Platform-specific open flags: Windows has `O_BINARY`, Linux and macOS have `O_NOFOLLOW`, so only one side runs on each system (both run across the local and CI runs). |
| `app/validation/model_inspector.py` | 58 | 1 of 2 | 59 | The `if __name__ == "__main__"` entry point. The system tests (and the spare inspectors) run it as a child process, which coverage does not follow. |

## 4. How to reproduce

```bash
cd backend
pytest --cov=app --cov-branch --cov-report=term-missing
```
The *BrPart* column in that output is the same data as section 3.
