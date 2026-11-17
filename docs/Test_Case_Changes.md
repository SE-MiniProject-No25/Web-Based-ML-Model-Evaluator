# Test Case Changes: original and updated Test Plan
## Web-Based ML Model Evaluator

The checklist asks that the **original test cases are updated to reflect the sprint changes**. This document shows that, case by case. There are two explicit versions of the Test Plan:

| Version | Revision | Date | File |
|---|---|---|---|
| **Original**, as submitted for Deliverable 1 | 1.1 | 27 September 2026 | [`deliverable-1/02_Test_Plan_v1.1_Deliverable1.md`](../deliverable-1/02_Test_Plan_v1.1_Deliverable1.md) (kept unchanged) |
| **Updated**, as built after the sprints | 1.5 | 5 November 2026 | [`deliverable-1/02_Test_Plan.md`](../deliverable-1/02_Test_Plan.md) |

The Test Plan's [Revision History](../deliverable-1/02_Test_Plan.md#revision-history) lists every revision with its commits (the first, revision 1.0 of 26 September, had 22 cases; revision 1.1 added three). The reasons for each change are the testing deviations T-01 to T-12 in the [Deviation Log](../docs/Deviation_Log.md#2a-testing-deviations-t).

## What changed

- **All 25 cases were updated.** No case was removed and none was added between revision 1.1 and revision 1.5.
- **What is verified did not change.** The *Requirement(s)* and *Type* columns are identical in both versions for every case. What changed is *how* each case is run and *what is expected*: the first version was written before anything was built, so the cases named no files, no endpoints and no concrete responses.
- **The updates are of four kinds:**
  1. **Concrete test data**: the reference files are named (`classification/model.joblib`, `negative/incompatible.csv`, a path-like name such as `../../evil.csv`).
  2. **Concrete steps**: the endpoint or the interface control is named (`GET /api/evaluations/{id}`, the Download Results button).
  3. **Exact expected results**: the HTTP status and the error code (`415 UNSUPPORTED_FILE_TYPE`, `413 FILE_TOO_LARGE`, `422 INVALID_MODEL`, `404 EVALUATION_NOT_FOUND`, `409 EVALUATION_NOT_COMPLETED`).
  4. **Behaviour that changed during the sprints**: TC-12 (the Download Results button was built), TC-15 (the memory limit on Windows), TC-17 (the authentication mechanism), TC-18 (cleanup on a timer) and TC-19 (acknowledgement measured at one request a second).
- **Outside the case table** the two versions differ only in the traceability matrix (the NFR-09 row now records the automated architecture check), a pointer to the results, and the sections added after the cases: the Document Control, the Revision History, section 9 (automated test mapping), section 10 (test execution record), section 11 (responsibilities), section 12 (schedule), section 13 (suspension and resumption criteria) and section 14 (test metrics).
- **Every updated case was run.** The result of each is in [section 10](../deliverable-1/02_Test_Plan.md#10-test-execution-record) of the updated plan and in the [System Validation Report](System_Validation_Report.md): 25 of 25 pass.

## Summary of the 25 cases

| Case | Test | What changed | Why |
|---|---|---|---|
| [TC-01](#tc-01-upload-model) | Upload model | Test Data, Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-02](#tc-02-upload-dataset) | Upload dataset | Test Data, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-03](#tc-03-unsupported-file) | Unsupported file | Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-04](#tc-04-size-limit-boundary) | Size limit boundary | Preconditions, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-05](#tc-05-missing-target-column) | Missing target column | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-06](#tc-06-invalid-task-type) | Invalid task type | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-07](#tc-07-empty-submission) | Empty submission | Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-08](#tc-08-classification-metrics) | Classification metrics | Test Data | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-09](#tc-09-regression-metrics) | Regression metrics | Test Data | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-10](#tc-10-status-lifecycle) | Status lifecycle | Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-11](#tc-11-incompatible-inputs) | Incompatible inputs | Test Data, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-12](#tc-12-download) | Download | Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-05](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-13](#tc-13-path-like-filename) | Path-like filename | Test Data, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-14](#tc-14-malformed-model) | Malformed model | Test Data, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-15](#tc-15-resource-limits) | Resource limits | Preconditions, Test Data, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-06](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-16](#tc-16-no-sensitive-errors) | No sensitive errors | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-17](#tc-17-authentication) | Authentication | Preconditions, Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-08](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-18](#tc-18-temporary-cleanup) | Temporary cleanup | Preconditions, Test Steps, Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-07](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-19](#tc-19-acknowledgement-time) | Acknowledgement time | Test Steps | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-09](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-20](#tc-20-determinism) | Determinism | Test Steps | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-21](#tc-21-usability) | Usability | Test Steps | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-11](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-22](#tc-22-unique-id-and-terminal-state) | Unique ID and terminal state | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-23](#tc-23-malformed-csv) | Malformed CSV | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-24](#tc-24-unknown-id) | Unknown ID | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |
| [TC-25](#tc-25-download-too-early) | Download too early | Expected Result | [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t) |

*Why:* **T-04** applies to every case (reworded to the application as built). The others add the reason a particular case changed after that: T-05 the Download Results button, T-06 the Windows memory limit, T-07 the retention timer, T-08 the authentication mechanism, T-09 the acknowledgement pace, T-11 the one-participant usability test.

## The cases, original beside updated


### TC-01: Upload model

**Requirements:** FR-01 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Data, Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Reference classification model | Reference classification model (`backend/tests/fixtures/classification/model.joblib`) |
| Test Steps | Upload a supported model file | Choose a supported model file (`.joblib` or `.pkl`) in the Upload step, or send it to `POST /api/evaluations` |
| Expected Result | Model is accepted and shown as ready for evaluation | Model is accepted and shown as ready for evaluation (the API answers `202`) |


### TC-02: Upload dataset

**Requirements:** FR-02 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Data, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Valid classification dataset | Valid classification dataset (`classification/data.csv`) |
| Expected Result | Dataset is accepted and its available columns are shown | Dataset is accepted and its available columns are shown (the Configure step lists the CSV header) |


### TC-03: Unsupported file

**Requirements:** FR-03, FR-04, NFR-04, NFR-10, SEC-01 (unchanged). **Type:** Security/Functional (unchanged). **Changed:** Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Upload an unsupported file type | Upload an unsupported file type (the browser blocks it before sending; the server check is tested through the API) |
| Expected Result | File is rejected before evaluation and a clear validation error is shown | File is rejected before evaluation with `415 UNSUPPORTED_FILE_TYPE` and a clear message; nothing is stored and no evaluation is created |


### TC-04: Size limit boundary

**Requirements:** FR-03, FR-04, NFR-06, NFR-10, SEC-01 (unchanged). **Type:** Boundary/Security (unchanged). **Changed:** Preconditions, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Preconditions | Upload limit is configured | Upload limit is configured (default 10 MB, `MLEVAL_MAX_UPLOAD_BYTES`) |
| Expected Result | The file at the limit is accepted; the larger file is rejected with a clear size-limit error and evaluation does not start | The file at the limit is accepted; the file one byte above is rejected with `413 FILE_TOO_LARGE` and a clear size-limit error, and no evaluation is created |


### TC-05: Missing target column

**Requirements:** FR-05, FR-07, SEC-08 (unchanged). **Type:** Functional/Security (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Configuration is rejected and evaluation cannot start | Configuration is rejected with `422 INVALID_TARGET_COLUMN` and evaluation cannot start |


### TC-06: Invalid task type

**Requirements:** FR-06, SEC-08 (unchanged). **Type:** Functional/Security (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Server rejects the request with a defined validation error | Server rejects the request with `422 INVALID_TASK_TYPE` |


### TC-07: Empty submission

**Requirements:** FR-16 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Click Evaluate without required model/dataset/configuration | Try to evaluate without the model, dataset or configuration (the Next button stays disabled), and send an incomplete request to the API |
| Expected Result | Evaluation does not start and missing inputs are identified | Evaluation does not start; the API answers `400 MISSING_REQUIRED_FIELD` naming each missing field |


### TC-08: Classification metrics

**Requirements:** FR-05, FR-06, FR-08, FR-09, FR-10 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Data. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Deterministic classification model/dataset pair with known expected metrics | Deterministic classification pair with known expected metrics (`classification/` fixtures and `expected_metrics.json`) |


### TC-09: Regression metrics

**Requirements:** FR-05, FR-06, FR-08, FR-09, FR-11 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Data. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Deterministic regression model/dataset pair with known expected metrics | Deterministic regression pair with known expected metrics (`regression/` fixtures and `expected_metrics.json`) |


### TC-10: Status lifecycle

**Requirements:** FR-12, FR-13, NFR-08 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Observe status and completed result | Observe the status (poll `GET /api/evaluations/{id}`) and the completed result |
| Expected Result | Status transitions through the defined lifecycle and result is displayed | Status moves `pending`, `running`, then `completed`, and the result is displayed |


### TC-11: Incompatible inputs

**Requirements:** FR-08, FR-12, FR-14 (unchanged). **Type:** Negative (unchanged). **Changed:** Test Data, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Incompatible model/dataset pair | Incompatible model/dataset pair (`classification/model.joblib` with `negative/incompatible.csv`), and a dataset with the wrong target column chosen |
| Expected Result | Status becomes failed and a safe, user-readable error is shown | Status becomes `failed` with error code `INCOMPATIBLE_INPUTS` and a safe message that names the missing and unused columns |


### TC-12: Download

**Requirements:** FR-15 (unchanged). **Type:** Functional (unchanged). **Changed:** Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-05](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Select Download Result | Click **Download Results** on the results screen (shown once the evaluation has completed), or request `GET /api/evaluations/{id}/download` |
| Expected Result | Structured result file is returned/downloaded | A JSON file is returned as an attachment (`evaluation-<id>.json`) with the ID, task type, target column, input filenames, metrics and timestamps |


### TC-13: Path-like filename

**Requirements:** FR-17, NFR-10, SEC-02 (unchanged). **Type:** Security (unchanged). **Changed:** Test Data, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | File with a path-like filename | File with a path-like filename such as `../../evil.csv` |
| Expected Result | Server uses a controlled storage name/path and does not write outside allowed storage | Server stores it under a random UUID name inside the storage directory and does not write outside it |


### TC-14: Malformed model

**Requirements:** FR-04, NFR-10, SEC-03 (unchanged). **Type:** Security (unchanged). **Changed:** Test Data, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Data | Malformed model file | Malformed model file (`negative/malformed_model.joblib`, and files that unpickle to something without `predict`) |
| Expected Result | Artifact is rejected before model execution and a clear validation error is shown | Artifact is rejected with `422 INVALID_MODEL` before it is used for evaluation, and a clear validation error is shown |


### TC-15: Resource limits

**Requirements:** NFR-10, SEC-04 (unchanged). **Type:** Security (unchanged). **Changed:** Preconditions, Test Data, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-06](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Preconditions | Resource limits configured | Resource limits configured (time limit 60 s by default, `MLEVAL_EVALUATION_TIMEOUT_SECONDS`; memory limit 2 GiB by default, `MLEVAL_EVALUATION_MEMORY_LIMIT_BYTES`, enforced on Linux and Windows) |
| Test Data | Model/dataset pair that exceeds the configured time or memory limit | A model that runs longer than the time limit; a model that allocates more memory than the memory limit |
| Expected Result | Request is stopped/rejected according to the configured policy | The evaluation ends `failed` with `RESOURCE_LIMIT_EXCEEDED` and a message naming the limit; the child process is killed |


### TC-16: No sensitive errors

**Requirements:** FR-04, FR-14, NFR-05, NFR-10, SEC-05 (unchanged). **Type:** Security (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Each response contains a safe error code/message and no raw trace, secret, or server path | Each response contains a safe error code/message and no raw trace, secret, or server path; the same holds for unknown URLs and unexpected server errors |


### TC-17: Authentication

**Requirements:** NFR-07, NFR-10, SEC-06 (unchanged). **Type:** Security (unchanged). **Changed:** Preconditions, Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-08](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Preconditions | Authentication is enabled | Authentication is enabled (`MLEVAL_AUTH_ENABLED=true` and `MLEVAL_API_KEY` set) |
| Test Steps | Call protected evaluation/result endpoint without credentials | Call `POST /api/evaluations`, `GET /api/evaluations/{id}` and `GET /api/evaluations/{id}/download` without credentials; then repeat with the key in `X-API-Key` or `Authorization: Bearer` |
| Expected Result | Request is rejected as unauthenticated | Requests without credentials are rejected with `401 UNAUTHENTICATED`; requests with the key succeed; `/api/health` stays open; if authentication is enabled with no key configured, every protected request is rejected |


### TC-18: Temporary cleanup

**Requirements:** FR-17, NFR-10, SEC-07 (unchanged). **Type:** Security (unchanged). **Changed:** Preconditions, Test Steps, Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-07](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Preconditions | Evaluation lifecycle completed | Retention period configured (`MLEVAL_RETENTION_SECONDS`, 3600 s by default) |
| Test Steps | Inspect temporary storage according to policy | Complete an evaluation, wait longer than the retention period, and inspect the storage directory (the cleanup runs at start-up, every `MLEVAL_CLEANUP_INTERVAL_SECONDS` (300 s by default) and after each submission) |
| Expected Result | Temporary artifacts are removed according to configured retention policy | Artifacts older than the retention period are deleted without waiting for a new request, newer ones are kept, and the files of an evaluation that is still pending or running are kept whatever their age |


### TC-19: Acknowledgement time

**Requirements:** NFR-02 (unchanged). **Type:** Performance (unchanged). **Changed:** Test Steps. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-09](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Send 10 valid evaluation requests and measure acknowledgement time | Send 10 valid evaluation requests one after another, one second apart (the pace of one user), and measure the time to the `202` (`backend/scripts/measure_ack_time.py`); the back-to-back time is also measured and reported |


### TC-20: Determinism

**Requirements:** FR-09, NFR-03 (unchanged). **Type:** Non-functional (unchanged). **Changed:** Test Steps. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Run identical evaluation three times | Run the identical evaluation three times (`backend/tests/test_determinism.py`) |


### TC-21: Usability

**Requirements:** NFR-01 (unchanged). **Type:** Usability (unchanged). **Changed:** Test Steps. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t), [T-11](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Test Steps | Ask user to perform upload → configure → evaluate → inspect result | Ask the user to perform upload → configure → evaluate → inspect result with no help; record whether each control was found (procedure and record sheet: `deliverable-1/usability-testing/`) |


### TC-22: Unique ID and terminal state

**Requirements:** FR-12, FR-18, NFR-08 (unchanged). **Type:** Functional (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Evaluation has a unique identifier and reaches completed or failed status | Evaluation has a unique random identifier (UUID) and reaches `completed` or `failed`, and a terminal status never changes |


### TC-23: Malformed CSV

**Requirements:** FR-04, NFR-10, SEC-03 (unchanged). **Type:** Security/Negative (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Dataset is rejected before model execution and a clear validation error is shown | Dataset is rejected with `422 MALFORMED_DATASET` before model execution and a clear validation error is shown |


### TC-24: Unknown ID

**Requirements:** FR-19 (unchanged). **Type:** Negative (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Each request returns a not-found error | Each request returns `404 EVALUATION_NOT_FOUND` |


### TC-25: Download too early

**Requirements:** FR-20 (unchanged). **Type:** Negative (unchanged). **Changed:** Expected Result. **Why:** [T-04](../docs/Deviation_Log.md#2a-testing-deviations-t).

| Part | Original (revision 1.1) | Updated (revision 1.5) |
|---|---|---|
| Expected Result | Download is rejected with a status error and no result file is returned | Download is rejected with `409 EVALUATION_NOT_COMPLETED` and no result file is returned |
