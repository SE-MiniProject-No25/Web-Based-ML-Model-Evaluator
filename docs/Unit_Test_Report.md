# Unit Test Report
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

## 1. What counts as a unit test

A **unit test** checks one component on its own: pure functions, a component with in-memory fakes, or a small application built inside the test. A **system test** goes through the whole application (the HTTP API, a real server, or a real model run in a child process); those are reported in the [System Validation Report](System_Validation_Report.md). The split is made once, in `backend/tests/conftest.py`, and tests carry the pytest markers `unit` and `system`.

## 2. Summary

| | Unit | System | All |
|---|---|---|---|
| Tests | 215 | 126 | 341 |
| Passed | 214 | 126 | 340 |
| Failed | 0 | 0 | 0 |
| Skipped | 1 | 0 | 1 |
| Run time | 26.8 s | 178 s | 205 s |


The unit tests alone cover **91.9% of lines** and **80.1% of branches** of `backend/app` and run in about 27 seconds. See the [Code Coverage Report](Code_Coverage_Report.md) and the [Branch Coverage Report](Branch_Coverage_Report.md).

## 3. Results by test file

| Test file | Component under test | Tests | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| `test_architecture.py` | Component boundaries (NFR-09) | 9 | 9 | 0 | 0 |
| `test_auth.py` | Optional API-key authentication middleware (US-11) | 37 | 37 | 0 | 0 |
| `test_component_edges.py` | Storage lifecycle edges, metrics, child environment, settings | 12 | 12 | 0 | 0 |
| `test_config.py` | Settings and environment overrides | 2 | 2 | 0 | 0 |
| `test_edge_paths.py` | Failed partial write, framework 5xx error, authentication settings lookup, lifespan events | 7 | 7 | 0 | 0 |
| `test_errors.py` | Error type, status table, safe error responses (US-09) | 39 | 39 | 0 | 0 |
| `test_metrics_service.py` | Metrics Service: classification and regression metrics | 8 | 8 | 0 | 0 |
| `test_model_inspector.py` | Model inspector run during validation (US-07) | 6 | 6 | 0 | 0 |
| `test_reference_fixtures.py` | Shared reference models and datasets (EN-02) | 11 | 11 | 0 | 0 |
| `test_result_service.py` | Result Service: lifecycle, IDs, concurrency | 13 | 13 | 0 | 0 |
| `test_retention.py` |  | 7 | 7 | 0 | 0 |
| `test_storage.py` | Temporary storage, permissions, retention cleanup (US-10) | 27 | 27 | 0 | 0 |
| `test_traceability.py` | Test Plan cases map to real tests | 3 | 3 | 0 | 0 |
| `test_validation_service.py` | Dataset parsing and child-process handling in validation | 18 | 18 | 0 | 0 |
| `test_worker.py` | Model worker process: every outcome it can report (US-04) | 16 | 15 | 0 | 1 |

## 4. Failures and skipped tests

No unit test failed.

Skipped:

- `test_worker.py::test_a_positive_memory_limit_is_applied_on_posix`: memory limits need the POSIX resource module

These need the POSIX `resource` module, so they only run on Linux and macOS (they run in CI).

## 5. What the unit tests cover well

- **Security-relevant code paths:** a hung or crashing model-inspection child, a worker killed without reporting, a half-failed upload that must not leave files behind, child-process environment without server secrets, path traversal in stored filenames, authentication edge cases, and error responses that must not leak internals.
- **The model worker and inspector** run in child processes during real use, which coverage cannot follow, so they are called in-process by `test_worker.py` and `test_model_inspector.py`. That is why they have real coverage figures.
- **Component boundaries** are enforced by `test_architecture.py` (NFR-09).

## 6. Known gaps

- No frontend unit tests (DEF-08).
- Memory-limit behaviour is only exercised on Linux and macOS.
- Lines that remain uncovered are listed per file in the Code Coverage Report, each with a reason.
