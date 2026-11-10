> **Superseded.** This is the Sprint 2 report from 3 November 2026. It was written before authentication, safe error responses, secure storage, the determinism tests and the usability test were merged, so its results and defect list are out of date. The current results are in the [System Validation Report](../docs/System_Validation_Report.md) and the other reports in [`docs/`](../docs/). It is kept for the record.

# Test Report
## Web-Based ML Model Evaluator

Result of executing the [Test Plan](../deliverable-1/02_Test_Plan.md) (25 cases, TC-01 to TC-25) against the implementation. Prepared for backlog item EN-03. Status of requirements is traced in the Test Plan §7.

| | |
|---|---|
| **Date** | 3 November 2026 |
| **Code under test** | `main` plus the Sprint 2 pull requests US-03, US-04, US-05, EN-07 and this one (EN-03) |
| **Local run** | Windows 11, Python 3.13, FastAPI 0.116, scikit-learn 1.9, one developer laptop |
| **CI run** | Ubuntu, Python 3.11, on every pull request (GitHub Actions) |
| **Reproduce** | `cd backend`, then `pip install -r requirements-dev.txt` and `python scripts/tc_report.py` |

## 1. Summary

| Result | Cases |
|---|---|
| **Pass** | **22** of 25: TC-01 to TC-16, TC-19, TC-20, TC-22 to TC-25 |
| **Fail** | **2**: TC-17 (authentication is not enforced), TC-18 (temporary files are never deleted). Both are features that are not built yet, recorded as defects DEF-01 and DEF-02 |
| **Not executed** | **1**: TC-21 (usability test with a fresh user; manual, see §5) |

The automated suite has 147 tests: 146 passed and 1 was skipped locally (the memory-limit test needs Linux; it ran and passed in CI, see TC-15). The suite is run on every pull request. TC-20 is covered by tests in an open pull request (#51); it was run against this branch for this report (§4).

The two failures are not test problems: with authentication switched on, unauthenticated requests are still accepted, and with a retention period of one second the uploaded files were still on disk after the evaluation finished. Both belong to Akash's Sprint 2 stories (US-11 and US-10).

## 2. Results by test case

"Tests" are automated tests in `backend/tests/`; the mapping is in `backend/tests/traceability.py` and is checked by `tests/test_traceability.py`.

| Case | Requirements | Result | Evidence |
|---|---|---|---|
| TC-01 Upload model | FR-01 | Pass | API accepts a supported model (1 test). UI half checked by hand, §6 |
| TC-02 Upload dataset | FR-02 | Pass | API accepts a valid CSV (2 tests); the UI lists the detected columns (manual, §6) |
| TC-03 Unsupported file | FR-03, FR-04, NFR-04, SEC-01 | Pass | `.exe` rejected with `415 UNSUPPORTED_FILE_TYPE`, nothing stored (1 test) |
| TC-04 Size limit boundary | FR-03, FR-04, NFR-06, SEC-01 | Pass | Exactly at the limit accepted, one byte over rejected with `413`, for model and dataset; the check stops reading early (5 tests) |
| TC-05 Missing target column | FR-05, FR-07, SEC-08 | Pass | Rejected with `422 INVALID_TARGET_COLUMN`; a valid column is accepted (2 tests) |
| TC-06 Invalid task type | FR-06, SEC-08 | Pass | `clustering`, `forecasting`, `dimensionality_reduction` rejected with `422 INVALID_TASK_TYPE` (3 tests) |
| TC-07 Empty submission | FR-16 | Pass | Each missing field gives `400 MISSING_REQUIRED_FIELD` naming it, nothing created (4 tests). UI half: manual, §6 |
| TC-08 Classification metrics | FR-05, FR-06, FR-08 to FR-10 | Pass | Reference model and data through the API reproduce the expected accuracy, precision, recall and F1 (2 tests) |
| TC-09 Regression metrics | FR-05, FR-06, FR-08, FR-09, FR-11 | Pass | Reference pair reproduces the expected MAE, MSE, RMSE and R² (2 tests) |
| TC-10 Status lifecycle | FR-12, FR-13, NFR-08 | Pass | `pending`, `running`, `completed` observed through the API, then the result (2 tests) |
| TC-11 Incompatible inputs | FR-08, FR-12, FR-14 | Pass | Ends `failed` with `INCOMPATIBLE_INPUTS` and a message naming the missing and unused columns; no paths in the message (3 tests) |
| TC-12 Download | FR-15 | Pass | JSON attachment whose metrics equal the reference values (2 tests) |
| TC-13 Path-like filename | FR-17, NFR-10, SEC-02 | Pass | `../../evil.csv` and `..\..\model.joblib` are stored under UUID names; nothing is written outside the storage directory (8 tests) |
| TC-14 Malformed model | FR-04, NFR-10, SEC-03 | Pass | Corrupt bytes, a pickled dict, an int and an object without `predict` are all rejected with `INVALID_MODEL` before evaluation (4 tests) |
| TC-15 Resource limits | NFR-10, SEC-04 | Pass | A model that sleeps 60 s is killed at the 3 s limit and the evaluation fails with `RESOURCE_LIMIT_EXCEEDED`, also through the API. A model that allocates 4 GB is stopped at a 1 GB limit. The memory test only runs on Linux and macOS: it was skipped locally on Windows and passed in CI (run 41641961993, 133 passed, 0 skipped). See DEF-04 |
| TC-16 No sensitive errors | FR-04, FR-14, NFR-05, SEC-05 | Pass | A validation error and a runtime error contain no trace, secret or server path; the real traceback appears only in the server log (3 tests). Unknown URLs are a known gap, DEF-03 |
| TC-17 Authentication | NFR-07, SEC-06 | **Fail** | Not implemented. With `auth_enabled=True`, a request without credentials returned `202` (submit) and `200` (status) instead of `401`. DEF-01 |
| TC-18 Temporary cleanup | FR-17, SEC-07 | **Fail** | Not implemented. With `retention_seconds=1`, both uploaded files were still in storage after the evaluation completed and 3 further seconds had passed. DEF-02 |
| TC-19 Acknowledgement time | NFR-02 | Pass | 10 requests, slowest 1.68 s (limit 2 s); thin margin, DEF-05. Numbers in §3 |
| TC-20 Determinism | FR-09, NFR-03 | Pass | The tests from pull request #51 (classification and regression, three identical runs each give identical metrics) passed against this branch (2 tests, §4). They are not on `main` yet |
| TC-21 Usability | NFR-01 | Not executed | Needs a fresh user. Procedure and record sheet in §5 |
| TC-22 Unique ID and terminal state | FR-12, FR-18, NFR-08 | Pass | Random UUIDs, unique across 100 and 5 submissions; a terminal status never changes, including under concurrent attempts (5 tests) |
| TC-23 Malformed CSV | FR-04, NFR-10, SEC-03 | Pass | Empty, whitespace-only, non-UTF-8, null-byte and ragged CSVs are rejected before any model runs (6 tests) |
| TC-24 Unknown ID | FR-19 | Pass | `404 EVALUATION_NOT_FOUND` for both status and download (2 tests) |
| TC-25 Download too early | FR-20 | Pass | Pending, running and failed evaluations give `409 EVALUATION_NOT_COMPLETED`, no file and no `Content-Disposition` (3 tests) |

## 3. Performance evidence (TC-19, NFR-02)

Measured with `backend/scripts/measure_ack_time.py` against a local server, time from sending the request to receiving the `202`, 10 valid requests one after another (Windows laptop):

| Request | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Seconds | 1.646 | 1.672 | 1.639 | 1.671 | 1.660 | 1.674 | 1.657 | 1.654 | 1.658 | 1.663 |

All are under 2 seconds (slowest 1.674 s, mean 1.659 s). The automated test run gave a slowest of 1.679 s. Almost all of the time is the model check done before the `202`: starting a child process and importing scikit-learn to unpickle the model takes about 1.6 s; everything else takes about 0.05 s. The requirement is met, with about 0.3 s to spare on this machine.

## 4. Determinism evidence (TC-20, NFR-03)

`backend/tests/test_determinism.py` from pull request #51 (Akshya, US-21) was run against this branch without being committed to it: 2 tests passed (classification and regression, three identical submissions each, metrics identical). Once #51 is merged, TC-20 should be added to `tests/traceability.py` so the table is generated automatically.

## 5. Manual test: usability (TC-21, NFR-01)

Not yet performed. It belongs to the usability story (US-22) and needs a person who has not seen the application.

**Procedure.** Give the user the running app and the demo files (`ml-evaluator-demo` or `backend/tests/fixtures/`). Say only: "Evaluate this model on this dataset and tell me the accuracy." Do not help; note where they hesitate.

**Record sheet.**

| Control | Found without help? (yes / no) | Notes |
|---|---|---|
| Model upload | | |
| Dataset upload | | |
| Task type and target column | | |
| Evaluate / run | | |
| Status | | |
| Results | | |
| Download | | |

Tester name and date: ______ Result (pass if every control was found without developer help): ______

## 6. Manual checks of the user interface

The browser half of TC-01, TC-02 and TC-07 has no automated test. On 3 November 2026 the combined interface (pull request #47) was exercised by hand in a browser against a running backend, using the demo files:

- After choosing a model and a CSV, the Configure step lists the detected columns (`5 column(s) detected: tenure_months, monthly_charge, support_calls, contract_years, churned`).
- With a file missing the Next button is disabled, so an empty submission cannot be sent from the page (TC-07, UI half).
- A model or CSV over 10 MB is refused in the browser with a size message.
- A classification run (accuracy 0.7389, F1 0.7314) and a regression run (MAE 24.54, R² 0.9231) both completed and displayed their metrics.
- A mismatched dataset ended `failed` with a readable message instead of raw JSON.
- With the backend stopped, submitting leaves the user on the Review step with an error message and the button usable again.

There is no automated frontend test yet.

## 7. Security validation (Test Plan §5.1)

| Area | Result |
|---|---|
| File validation | Pass: unsupported and malformed files are rejected before execution (TC-03, TC-14, TC-23) |
| Size limits | Pass (TC-04) |
| Path handling | Pass (TC-13) |
| Input validation | Pass: task type and target are checked on the server (TC-05, TC-06) |
| Resource protection | Pass on Linux and macOS; time limit only on Windows (TC-15, DEF-04) |
| Error disclosure | Pass for validation and runtime errors (TC-16); unknown URLs still return the framework's default error body (DEF-03) |
| Temporary data | **Fail** (TC-18, DEF-02) |
| Authentication | **Fail** (TC-17, DEF-01) |

Known limitation, accepted and documented in the README: a model file is a pickle and runs code when loaded. Models are loaded only in a child process with a sanitized environment, a time limit and (Linux and macOS) a memory limit. That is process isolation, not a sandbox, so a malicious model still runs with the server user's privileges.

## 8. Exit criteria (Test Plan §4.3)

| Criterion | Met? |
|---|---|
| All mandatory test cases have been executed | **No.** 24 of 25 have been executed; TC-21 needs a fresh user (§5) |
| All critical functional requirements have passing tests or documented defects | Yes. FR-01 to FR-16 and FR-18 to FR-20 pass; FR-17 passes for isolation (TC-13) and has a documented defect for cleanup (DEF-02) |
| Security validation cases have been executed | Yes. TC-03, TC-04, TC-13 to TC-18 and TC-23 were executed; TC-17 and TC-18 fail and are documented |
| Traceability is complete | Yes. All 25 cases map to tests or a documented reason, checked by `tests/test_traceability.py`; the RTM in the Test Plan §7 is current |
| Unresolved defects are documented with severity and status | Yes, §9 |

So the exit criteria are **not yet fully met**: TC-21 has not been run, and two security cases fail until US-10 and US-11 are built.

## 9. Defects

| ID | Defect | Requirement | Severity | Status | Owner |
|---|---|---|---|---|---|
| DEF-01 | Authentication is not enforced. The `auth_enabled` setting exists but nothing reads it, so switching it on gives a false sense of protection | NFR-07, SEC-06 (TC-17) | High | Open | Akash, US-11 |
| DEF-02 | Uploaded model and dataset files are never deleted; `retention_seconds` is not used. Disk use grows and user data stays on the server | FR-17, SEC-07 (TC-18) | High | Open | Akash, US-10 |
| DEF-03 | Unknown URLs and unsupported methods return the framework's `{"detail": ...}` instead of the standard error format. No sensitive data is exposed | NFR-05, SEC-05 (TC-16) | Low | Open | Akash, US-09 |
| DEF-04 | The memory limit is not enforced on Windows (no equivalent for a plain child process); only the time limit applies there | SEC-04 (TC-15) | Medium | Accepted, documented in the README | Adyanth |
| DEF-05 | Acknowledgement time is within the limit with only about 0.3 s to spare on Windows, dominated by the model check before the `202`. Options: a warm worker with scikit-learn already loaded, or checking the model after the `202` | NFR-02 (TC-19) | Low | Open, monitor | Adyanth |
| DEF-06 | A malicious model still runs code with the server user's privileges (process isolation is not a sandbox) | SEC-03, SEC-04 | High (inherent to accepting pickles) | Accepted, documented as a known limitation | Team |

## 10. Changes to the Test Plan and RTM

- §7 now notes that NFR-09 is checked automatically by `backend/tests/test_architecture.py` as well as by architecture review, and points to this report and to `backend/tests/traceability.py`.
- The Architecture document was corrected during this sprint (example IDs are UUIDs, §10.3 specifies the download file); no requirement changed.
- Nothing else in the RTM changed: every requirement still maps to the cases listed in §7 of the Test Plan.
