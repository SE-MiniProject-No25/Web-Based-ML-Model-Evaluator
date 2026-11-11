# System Validation Report
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

Result of executing the [Test Plan](../deliverable-1/02_Test_Plan.md) (25 cases, TC-01 to TC-25) against the complete application. It replaces `planning/Test_Report.md` (3 November), which was written before authentication, safe error responses, secure storage, the determinism tests and the usability test were merged.

## 1. Summary

| Result | Cases |
|---|---|
| **Pass** | **25 of 25**: TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25. 24 are automated; TC-21 is a manual test with one participant |
| **Fail** | 0 |
| Of those, with a limitation | TC-15 (memory limit not enforced on Windows), TC-18 (cleanup runs on the next submission, not on a timer), TC-21 (see section 5) |

The automated suite has 341 tests: 340 passed, 0 failed, 1 skipped (the memory-limit tests only run on Linux, in CI). Since the previous report, authentication (TC-17) and cleanup of temporary files (TC-18) have been built and now pass, so the two failures recorded then are closed.

## 2. Results by test case

| Case | What | Result | Automated tests passed | Note |
|---|---|---|---|---|
| TC-01 | Upload model | Pass | 1/1 | API accepts a supported model. UI checked by hand (section 6). |
| TC-02 | Upload dataset | Pass | 2/2 | API accepts a valid CSV; the UI lists the detected columns (section 6). |
| TC-03 | Unsupported file | Pass | 1/1 |  |
| TC-04 | Size limit boundary | Pass | 5/5 |  |
| TC-05 | Missing target column | Pass | 2/2 |  |
| TC-06 | Invalid task type | Pass | 3/3 |  |
| TC-07 | Empty submission | Pass | 4/4 | Each missing field gives `400 MISSING_REQUIRED_FIELD`. In the UI the Next button stays disabled (section 6). |
| TC-08 | Classification metrics | Pass | 2/2 |  |
| TC-09 | Regression metrics | Pass | 2/2 |  |
| TC-10 | Status lifecycle | Pass | 2/2 |  |
| TC-11 | Incompatible inputs | Pass | 3/3 |  |
| TC-12 | Download | Pass | 2/2 | Download works through the API and through the interface's Download Results button (section 6). |
| TC-13 | Path-like filename | Pass | 11/11 |  |
| TC-14 | Malformed model | Pass | 4/4 |  |
| TC-15 | Resource limits | Pass | 4/4 | Time limit proven end to end; memory limit proven on Linux (CI) and on Windows (job object, TEST-10). |
| TC-16 | No sensitive errors | Pass | 5/5 | Validation errors, runtime errors, unknown URLs and unexpected exceptions leak no trace, secret or path. |
| TC-17 | Authentication | Pass | 7/7 | Optional API key (`X-API-Key` or `Authorization: Bearer`); fails secure if enabled with no key. |
| TC-18 | Temporary cleanup | Pass | 7/7 | Expired files are removed at start-up, on a timer and after each submission; files of unfinished evaluations are kept (TEST-05). |
| TC-19 | Acknowledgement time | Pass | 1/1 | Slowest of 10: 1.62 s against the 2 s limit (section 3). |
| TC-20 | Determinism | Pass | 2/2 | Three identical runs give identical metrics, classification and regression. |
| TC-21 | Usability | Pass (manual) | - | A person outside the team completed the workflow unaided; see section 5 for the caveats. |
| TC-22 | Unique ID, terminal state | Pass | 5/5 |  |
| TC-23 | Malformed CSV | Pass | 6/6 |  |
| TC-24 | Unknown ID | Pass | 2/2 |  |
| TC-25 | Download too early | Pass | 3/3 |  |

Which tests cover each case is recorded in `backend/tests/traceability.py` and checked by `tests/test_traceability.py`.

## 3. Performance (TC-19, NFR-02)

10 valid requests one after another against a local server, seconds until the `202`:

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|
| 1.152 | 0.123 | 1.624 | 0.136 | 1.581 | 0.161 | 1.563 | 0.168 | 1.567 | 0.165 |

Back to back: slowest 1.624 s, mean 0.824 s; the limit is 2 s. All are within the limit, with 0.38 s to spare in the worst case.

**One second apart** (a person using the interface cannot submit faster): 0.165 | 0.124 | 0.130 | 0.135 | 0.145 | 0.138 | 0.126 | 0.141 | 0.159 | 0.124; slowest 0.165 s.

Almost all of the time used to be the model check before the `202`: a new child process importing scikit-learn (about 1.6 s). Since TEST-04 (#91), two spare inspector processes wait with scikit-learn already imported, and each model is still checked in its own fresh process. At a normal pace every request gets a ready spare; back-to-back requests faster than one a second can still wait for a new spare's import, which is why the back-to-back figure stays higher (DEF-05). The automated TC-19 test (`test_ack_time.py`) sends its requests one second apart: back to back, a two-core CI machine took up to 2.3 s on every second request, while waiting for a spare that had only just started.

## 4. Determinism (TC-20, NFR-03)

The tests in `tests/test_determinism.py` submit the same model and dataset three times for classification and for regression and require identical metrics. Both pass.

## 5. Usability (TC-21, NFR-01)

The usability test is written up in [`deliverable-1/usability-testing/US-22_Usability_Test_Report.md`](../deliverable-1/usability-testing/US-22_Usability_Test_Report.md). One person outside the team completed the workflow (upload, configure, evaluate, inspect the result) in about two minutes without help, and found the evaluate button easily. Improvement suggestions: clearer guidance on which files to choose, plain-language descriptions of the options, and explanations of the metrics.

The report has been corrected (11 Nov 2026) from the git history: the test took place on or before 3 November, on `main` at `c280412`. That build had no download control (the Download Results button came in pull request #62 on 10 November), so the remark that the participant "did not notice the download control" records a missing feature, since added. The metric explanations (#66) answer the third suggestion.

With one participant this is an indication, not a statistically meaningful result; the planned repeat with three people did not take place before the freeze (Deviation Log P-05). TC-21 is recorded as a **pass** for the primary workflow, with that caveat.

## 6. The user interface in a real browser

The browser half of TC-01, TC-02, TC-07, TC-08, TC-09, TC-11 and TC-12 is automated in `e2e/test_workflow.py` (TEST-07): Playwright drives Chromium against the real frontend and a real backend started for the run, with the demo inputs, and the tests run in CI. They check that:

- a classification run and a regression run show their metrics in the table (with the explanations) and the chart, with the expected values;
- **Download Results** saves `evaluation-<id>.json` with the status, the target column and the same accuracy as the screen;
- a malformed CSV is rejected and the message is shown next to the dataset field, with no download offered;
- a mismatched dataset ends *failed* with a message naming the missing and unused columns;
- a `.txt` model is refused as soon as it is chosen, and the next step stays disabled;
- with the backend unreachable, submitting shows "Unable to connect to the evaluation server".

Run them with `python -m pytest e2e` (see the README). The component tests in `frontend/src/test/` cover the same screens at a finer grain (TEST-01).

## 7. Security validation (Test Plan 5.1)

| Area | Result |
|---|---|
| File validation | Pass: unsupported and malformed files rejected before execution (TC-03, TC-14, TC-23) |
| Size limits | Pass (TC-04) |
| Path handling | Pass (TC-13) |
| Input validation | Pass: task type and target checked on the server (TC-05, TC-06) |
| Resource protection | Pass: time and memory limits on Linux, macOS and Windows (TC-15) |
| Error disclosure | Pass (TC-16): standard error format everywhere, including unknown URLs and unexpected exceptions |
| Temporary data | Pass: removed on a timer, never while in use (TC-18) |
| Authentication | Pass (TC-17); off by default, so a deployment must switch it on |

Accepted limitation, documented in the README: a model file is a pickle and runs code when loaded. Models are only opened in a child process with a sanitized environment and limits. That is process isolation, not a sandbox (DEF-06).

## 8. Exit criteria (Test Plan 4.3)

| Criterion | Met? |
|---|---|
| All mandatory test cases have been executed | Yes. All 25 were executed; TC-21 as a manual test. |
| Critical functional requirements have passing tests or documented defects | Yes. FR-01 to FR-20 pass at the API, and FR-15 also in the interface (Download Results button). |
| Security validation cases have been executed | Yes. TC-03, TC-04, TC-13 to TC-18 and TC-23 all pass. |
| Traceability is complete | Yes. All 25 cases map to tests or a manual record, checked automatically. |
| Unresolved defects are documented with severity and status | Yes, section 9. |

The exit criteria are met. Every defect is closed except DEF-06, the accepted pickle limitation.

## 9. Defects

| ID | Defect | Severity | Status |
|---|---|---|---|
| DEF-01 | Authentication not enforced | High | **Closed** by US-11 (pull request #58); TC-17 passes |
| DEF-02 | Uploaded files were never deleted | High | **Closed**: US-10 (#57) removes expired files; since TEST-05 (#89) also at start-up and every 300 s, without waiting for a request |
| DEF-03 | Unknown URLs returned the framework's default error body | Low | **Closed** by US-09 (#56); verified: `GET /api/nope` gives `404 {"error": {"code": "NOT_FOUND", ...}}` |
| DEF-04 | Memory limit not enforced on Windows | Medium | **Closed** by TEST-10 (#90): a Windows job object limits the evaluation process; `test_memory_limit.py` |
| DEF-05 | Acknowledgement margin was small (about 1.7 s of 2 s), dominated by the model check before the `202` | Low | **Closed** by TEST-04 (#91): about 0.17 s at a normal pace; back to back 1.62 s, still within 2 s |
| DEF-06 | A malicious model still runs code with the server user's privileges (pickle) | High (inherent) | Accepted, documented |
| DEF-07 | The usability report has no test date, so its remark about a download control cannot be tied to a build | Low | **Closed**: date and build added from the git history; the build tested had no download control (added in #62). One participant only (Deviation Log P-05) |
| DEF-08 | The frontend has no automated tests and no coverage figures | Medium | **Closed** by TEST-01 (#92): Vitest component and API tests with coverage (figures at the top of this report), run in CI; the whole workflow is also tested in a browser by TEST-07 (#93) |
| DEF-09 | The interface had no control to download results, so TC-12 was only met through the API | Medium | **Closed** by US-17 (pull request #62); verified: the button appears once an evaluation completes and saves `evaluation-<id>.json` with every field |
| DEF-10 | The retention cleanup did not skip files of an evaluation that is still running | Low | **Closed** by TEST-05 (#89): every sweep keeps the files of pending and running evaluations; `test_retention.py` |
| DEF-11 | Binary classes not labelled 0 and 1 (`yes`/`no`, `ham`/`spam`) failed: precision, recall and F1 assumed the positive class is 1 | High | **Closed** by TEST-11: the positive class is 1, otherwise the label that sorts last; the results screen says so |
| DEF-12 | A CSV with spaces after the commas (`a, b, label`) was rejected with `INVALID_TARGET_COLUMN`, because the interface sends the trimmed column name | Medium | **Closed** by TEST-11: names are compared without surrounding spaces |
| DEF-13 | An Excel byte-order mark made the first column `\ufefflabel`, so a target in the first column was rejected | Medium | **Closed** by TEST-11: the file is read as `utf-8-sig` |
| DEF-14 | A semicolon- or tab-separated file was rejected with a misleading `INVALID_TARGET_COLUMN` (the interface detected the separator, the server did not) | Low | **Closed** by TEST-11: both reject it, naming the separator |
| DEF-15 | Empty cells in the target or a feature, or text in a numeric column, ended as the generic "could not be completed" | Medium | **Closed** by TEST-11: `INCOMPATIBLE_INPUTS` naming the count or the columns (only when the model fails; a pipeline that fills empty cells still works) |
| DEF-16 | A text target with Regression, or a regression model with Classification, ended as the generic failure | Medium | **Closed** by TEST-11: `INCOMPATIBLE_INPUTS` saying which task type to choose |
| DEF-17 | The regression chart drew MSE and R² on one scale, so R² was invisible next to MSE | Low | **Closed** by TEST-11: scores are drawn from 0 to 1, MAE and RMSE share a scale, MSE is in the table only |

### Exploratory testing (TEST-11)

Unusual inputs were tried through the API and the interface: labels other than 0 and 1 and text labels, three text classes, empty cells in the target and in features, text in a numeric column, a header with spaces, a byte-order mark, semicolon and tab separators, a one-row dataset, a header-only dataset, 500 feature columns, a text target with Regression, a regression model with Classification, the same submission repeated, two submissions at the same moment on a real server, and unusual filenames (spaces, non-Latin letters, `..\\`, upper-case extensions). DEF-11 to DEF-17 were found and fixed; everything else already behaved. Every input is kept as a test in `tests/test_edge_case_inputs.py`.

## 10. Changes to test cases

The detailed test cases in [Test Plan section 8](../deliverable-1/02_Test_Plan.md) were updated to match what was built (authentication mechanism, retention, limits, download through the API). A table in section 9 of the Test Plan links each case to its automated tests.
