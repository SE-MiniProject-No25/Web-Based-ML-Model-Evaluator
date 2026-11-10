# System Validation Report
## Web-Based ML Model Evaluator

| | |
|---|---|
| **Date** | 10 November 2026 |
| **Code** | `main` at commit `a6669ab3`, plus the tests and documents added by the pull request that contains these reports |
| **Environment** | Windows 11, Python 3.13.7, pytest 9.1.1, coverage.py 7.17.2, FastAPI 0.116.2, scikit-learn 1.9.1 |
| **Reproduce** | `cd backend`, `pip install -r requirements-dev.txt`, `python scripts/generate_reports.py` |


**Scope.** These reports cover the backend (`backend/app`). The frontend has no automated tests, so it has no unit-test or coverage figures; it was checked by hand against a running backend (System Validation Report, section 6). Adding frontend tests is listed as a defect (DEF-08).

Result of executing the [Test Plan](../deliverable-1/02_Test_Plan.md) (25 cases, TC-01 to TC-25) against the complete application. It replaces `planning/Test_Report.md` (3 November), which was written before authentication, safe error responses, secure storage, the determinism tests and the usability test were merged.

## 1. Summary

| Result | Cases |
|---|---|
| **Pass** | **25 of 25**: TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16, TC-17, TC-18, TC-19, TC-20, TC-21, TC-22, TC-23, TC-24, TC-25. 24 are automated; TC-21 is a manual test with one participant |
| **Fail** | 0 |
| Of those, with a limitation | TC-12 (the API download works; the interface has no download control), TC-15 (memory limit not enforced on Windows), TC-18 (cleanup runs on the next submission, not on a timer), TC-21 (see section 5) |

The automated suite has 288 tests: 286 passed, 0 failed, 2 skipped (the memory-limit tests only run on Linux, in CI). Since the previous report, authentication (TC-17) and cleanup of temporary files (TC-18) have been built and now pass, so the two failures recorded then are closed.

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
| TC-12 | Download | Pass | 2/2 | Download works through the API. **The interface has no download control (DEF-09).** |
| TC-13 | Path-like filename | Pass | 11/11 |  |
| TC-14 | Malformed model | Pass | 4/4 |  |
| TC-15 | Resource limits | Pass | 2/3, 1 skipped | Time limit proven end to end; memory limit proven on Linux (CI) and not enforced on Windows (DEF-04). |
| TC-16 | No sensitive errors | Pass | 5/5 | Validation errors, runtime errors, unknown URLs and unexpected exceptions leak no trace, secret or path. |
| TC-17 | Authentication | Pass | 7/7 | Optional API key (`X-API-Key` or `Authorization: Bearer`); fails secure if enabled with no key. |
| TC-18 | Temporary cleanup | Pass | 4/4 | Expired files are removed. The sweep runs when a new evaluation is submitted, not on a timer (DEF-02, DEF-10). |
| TC-19 | Acknowledgement time | Pass | 1/1 | Slowest of 10: 1.89 s against the 2 s limit (section 3). |
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
| 1.675 | 1.601 | 1.604 | 1.659 | 1.639 | 1.614 | 1.639 | 1.652 | 1.724 | 1.893 |

Slowest 1.893 s, mean 1.670 s; the limit is 2 s. All are within the limit, with 0.11 s to spare in the worst case. Almost all of the time is the model check done before the `202` (a child process loads scikit-learn to open the model), see DEF-05. The figure varies from run to run: on 10 November three further runs on an otherwise idle machine had slowest times of 1.74, 1.72 and 1.82 s, and this run, which started right after the test suite, 1.89 s. Treat the margin as roughly 0.1 to 0.3 s on this laptop.

## 4. Determinism (TC-20, NFR-03)

The tests in `tests/test_determinism.py` submit the same model and dataset three times for classification and for regression and require identical metrics. Both pass.

## 5. Usability (TC-21, NFR-01)

The usability test is written up in [`deliverable-1/usability-testing/US-22_Usability_Test_Report.md`](../deliverable-1/usability-testing/US-22_Usability_Test_Report.md). One person outside the team completed the workflow (upload, configure, evaluate, inspect the result) in about two minutes without help, and found the evaluate button easily. Improvement suggestions: clearer guidance on which files to choose, plain-language descriptions of the options, and explanations of the metrics.

Two things in that report need correcting before it is relied on:

- It says the participant "did not notice the download control", but **the interface has no download control** (US-17 is not built), so there was nothing to notice. Either a different build was tested or the line should be removed.
- The test date is still the placeholder `[Enter actual test date]`.

With one participant this is an indication, not a statistically meaningful result. TC-21 is recorded as a **pass** for the primary workflow, with those caveats (DEF-07).

## 6. Manual checks of the user interface

The browser half of TC-01, TC-02 and TC-07 has no automated test. The interface (the step-by-step version from pull request #47) was exercised by hand against a running backend with the reference files:

- After choosing a model and a CSV, the Configure step lists the detected columns.
- With a file missing, the Next button is disabled, so an empty submission cannot be sent from the page.
- A model or CSV over 10 MB is refused in the browser with a size message.
- A classification run and a regression run completed and displayed their metrics (screenshots in `planning/demo/`).
- A mismatched dataset ended *failed* with a message naming the missing and unused columns; a corrupt model and a malformed CSV were rejected with a plain message on the review step.
- With the backend stopped, submitting keeps the user on the review step with an error and the button usable.

## 7. Security validation (Test Plan 5.1)

| Area | Result |
|---|---|
| File validation | Pass: unsupported and malformed files rejected before execution (TC-03, TC-14, TC-23) |
| Size limits | Pass (TC-04) |
| Path handling | Pass (TC-13) |
| Input validation | Pass: task type and target checked on the server (TC-05, TC-06) |
| Resource protection | Pass on Linux and macOS; time limit only on Windows (TC-15, DEF-04) |
| Error disclosure | Pass (TC-16): standard error format everywhere, including unknown URLs and unexpected exceptions |
| Temporary data | Pass with a limitation (TC-18, DEF-02) |
| Authentication | Pass (TC-17); off by default, so a deployment must switch it on |

Accepted limitation, documented in the README: a model file is a pickle and runs code when loaded. Models are only opened in a child process with a sanitized environment and limits. That is process isolation, not a sandbox (DEF-06).

## 8. Exit criteria (Test Plan 4.3)

| Criterion | Met? |
|---|---|
| All mandatory test cases have been executed | Yes. All 25 were executed; TC-21 as a manual test. |
| Critical functional requirements have passing tests or documented defects | Yes. FR-01 to FR-20 pass at the API; FR-15 has a documented gap in the interface (DEF-09). |
| Security validation cases have been executed | Yes. TC-03, TC-04, TC-13 to TC-18 and TC-23 all pass. |
| Traceability is complete | Yes. All 25 cases map to tests or a manual record, checked automatically. |
| Unresolved defects are documented with severity and status | Yes, section 8. |

The exit criteria are met. Open defects are low or medium severity, except the accepted pickle limitation.

## 9. Defects

| ID | Defect | Severity | Status |
|---|---|---|---|
| DEF-01 | Authentication not enforced | High | **Closed** by US-11 (pull request #58); TC-17 passes |
| DEF-02 | Uploaded files were never deleted | High | **Closed with a limitation**: US-10 (#57) removes expired files, but only when a new evaluation is submitted; with no new requests they stay until the next one. Low severity now |
| DEF-03 | Unknown URLs returned the framework's default error body | Low | **Closed** by US-09 (#56); verified: `GET /api/nope` gives `404 {"error": {"code": "NOT_FOUND", ...}}` |
| DEF-04 | Memory limit not enforced on Windows | Medium | Accepted, documented in the README |
| DEF-05 | Acknowledgement margin is small on Windows (1.89 s of 2 s), dominated by the model check before the `202` | Low | Open, monitor |
| DEF-06 | A malicious model still runs code with the server user's privileges (pickle) | High (inherent) | Accepted, documented |
| DEF-07 | The usability report names a download control that does not exist and has no test date | Low | Open, owner Akshya |
| DEF-08 | The frontend has no automated tests and no coverage figures | Medium | Open |
| DEF-09 | The interface has no control to download results (US-17), so TC-12 is only met through the API | Medium | Open, owner Akshath |
| DEF-10 | The retention cleanup does not skip files of an evaluation that is still running. With the defaults (retention 3600 s, evaluation limit 60 s) this cannot happen, but a retention shorter than a run could delete files mid-evaluation | Low | Open, owner Akash |

## 10. Changes to test cases

The detailed test cases in [Test Plan section 8](../deliverable-1/02_Test_Plan.md) were updated to match what was built (authentication mechanism, retention, limits, download through the API). A table in section 9 of the Test Plan links each case to its automated tests.
