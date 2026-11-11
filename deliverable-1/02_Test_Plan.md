# Software Test Plan
## Web-Based ML Model Evaluator

> **Deviations (as built).** The test cases in section 8 were updated to match what was built (Part 3). Changes that affect testing are in the [Deviation Log](../docs/Deviation_Log.md): TC-15 memory limit on all three systems ([D-07](../docs/Deviation_Log.md#1-design-deviations)), TC-18 retention on a timer (D-06), TC-19 acknowledgement time with spare inspectors (D-11), and the interface halves of TC-01, TC-02 and TC-07 automated in the browser (D-16).


## 1. Introduction

### 1.1 Purpose

This Test Plan defines the verification and validation approach for the Web-Based ML Model Evaluator. It covers functional behavior, non-functional properties, security validation, and traceability to the [Software Requirements Specification](01_SRS.md).

### 1.2 Scope

Testing covers:

- input upload and validation;
- evaluation configuration;
- classification and regression metric calculation;
- evaluation lifecycle/status;
- result presentation and download;
- error handling;
- performance and determinism;
- security controls for uploaded artifacts and evaluation requests.

Model-training correctness is outside scope because the system evaluates already-trained models.

### 1.3 Test Objectives

1. Verify that every mandatory functional requirement has test coverage.
2. Verify measurable non-functional requirements where practical.
3. Validate security objectives and requirements.
4. Detect invalid-input and error-handling failures before submission.
5. Maintain bidirectional traceability between requirements and test cases.

### 1.4 Test Environment

- Modern desktop browser.
- Local or designated development server.
- Supported Python/ML runtime used by the implementation.
- Controlled CSV datasets for classification and regression.
- Small deterministic reference models for expected metric calculations.

### 1.5 Test Deliverables

- Test Plan.
- Detailed test cases.
- Test execution results.
- Defect records, if applicable.
- Updated traceability matrix.

---

## 2. Test Strategy

### 2.1 Test Levels

**Unit testing:** Individual validation, metric, API, and utility functions.

**Integration testing:** UI/API, API/evaluation engine, and evaluation/result-storage interactions.

**System testing:** Complete browser-to-result evaluation workflow.

**Security validation:** File, path, input, resource-limit, and information-disclosure checks.

### 2.2 Test Types

- Functional testing
- Negative testing
- Boundary-value testing
- Integration testing
- System testing
- Performance testing
- Usability testing
- Security testing
- Regression testing

### 2.3 Test Data

Test data shall include:

- reference classification and regression models in each supported model format;
- valid classification dataset;
- valid regression dataset;
- missing-target dataset;
- malformed CSV;
- malformed (corrupted or truncated) model file;
- unsupported file;
- files exactly at and one byte above the configured size limit;
- file with a path-like filename (e.g. `../../evil.csv`);
- invalid task type;
- incompatible model/dataset pair (dataset features do not match the model);
- deterministic model/dataset pair with known expected metrics;
- unknown evaluation identifier.

---

## 3. Test Cases and Test Procedures

The detailed cases are specified in [Section 8 — Detailed Test Cases](#8-detailed-test-cases).

Each test case specifies:

- test ID;
- related requirement(s);
- test type;
- preconditions;
- test data;
- steps;
- expected result, which is the pass criterion for the case under the pass/fail rules in Section 4.4.

### 3.1 Functional Coverage

Functional testing shall cover:

1. model upload;
2. dataset upload;
3. file validation;
4. target selection;
5. task selection;
6. missing-input prevention;
7. classification metrics;
8. regression metrics;
9. evaluation status;
10. successful result display;
11. evaluation failure handling;
12. result download;
13. evaluation metadata/identifier.

### 3.2 Negative and Boundary Testing

At minimum, tests shall cover:

- empty submission;
- unsupported extension;
- malformed model;
- malformed CSV;
- missing target column;
- invalid task type;
- oversized file;
- incompatible model/dataset;
- evaluation failure;
- unavailable result identifier;
- result download requested before evaluation completion.

---

## 4. Test Environment, Tools and Schedule

### 4.1 Tools

The implementation team may use:

- browser developer tools;
- API client such as Postman/Thunder Client/cURL;
- unit-test framework appropriate to the backend;
- test runner appropriate to the frontend;
- static analysis/linting tools;
- Git for version control.

### 4.2 Entry Criteria

Testing may begin when:

- the corresponding feature is implemented;
- application starts successfully;
- required test data is available;
- known blocking build errors are resolved.

### 4.3 Exit Criteria

Testing for the deliverable is complete when:

- all mandatory test cases have been executed;
- all critical functional requirements have passing tests or documented defects;
- security validation cases have been executed;
- traceability is complete;
- unresolved defects are documented with severity and status.

### 4.4 Pass/Fail Rules

A test passes only when the observed behavior satisfies its stated expected result. A test fails when the required behavior is absent, incorrect, unsafe, or materially different from the expected result.

---

## 5. Test Procedures

### 5.1 Security Validation

Security validation shall specifically verify:

| Security Area | Validation |
|---|---|
| File validation | Unsupported types and malformed files are rejected before execution. |
| Size limits | Oversized uploads are rejected. |
| Path handling | User filenames cannot control server storage paths. |
| Input validation | Target/task values are validated server-side. |
| Resource protection | Evaluation requests are subject to configured limits. |
| Error disclosure | Client responses do not contain raw traces, secrets, or internal paths. |
| Temporary data | Temporary artifacts follow the configured cleanup policy. |
| Authentication | Protected endpoints reject unauthenticated requests when authentication is configured. |

### 5.2 Performance Validation

NFR-02 shall be tested using 10 repeated evaluation-request submissions under normal local deployment conditions. The request acknowledgement time shall be measured and compared with the 2-second requirement.

### 5.3 Determinism Validation

NFR-03 shall be tested by executing an identical model/dataset/task/configuration combination at least three times and comparing the metric outputs.

### 5.4 Usability Validation

A representative user shall attempt the primary workflow without developer assistance. The test observer shall record whether upload, configuration, run, status, result, and download controls are identifiable.

---

## 6. Test Risks

| Risk | Mitigation |
|---|---|
| Model format incompatibility | Define supported formats and validate before execution. |
| Large evaluation input | Enforce size/resource limits. |
| Metric mismatch | Use reference datasets with manually verified expected values. |
| Environment differences | Record runtime and dependency versions. |
| Unsafe uploaded model execution | Restrict supported formats and isolate evaluation execution as far as the deployment permits. |

---

## 7. Requirements Traceability Matrix

| SRS ID | Description (short) | Test Case(s) | Architecture / Design |
|---|---|---|---|
| FR-01 | Model upload | TC-01 | Web UI, API, Validation |
| FR-02 | Dataset upload | TC-02 | Web UI, API, Validation |
| FR-03 | File validation | TC-03, TC-04 | Validation, Security Policy |
| FR-04 | Validation errors | TC-03, TC-04, TC-14, TC-16, TC-23 | Validation, API Error Handler |
| FR-05 | Target selection | TC-05, TC-08, TC-09 | Web UI, Validation |
| FR-06 | Task selection | TC-06, TC-08, TC-09 | Web UI, Validation |
| FR-07 | Target exists | TC-05 | Validation |
| FR-08 | Execute model | TC-08, TC-09, TC-11 | Evaluation Service |
| FR-09 | Calculate metrics | TC-08, TC-09, TC-20 | Metrics Service |
| FR-10 | Classification metrics | TC-08 | Metrics Service |
| FR-11 | Regression metrics | TC-09 | Metrics Service |
| FR-12 | Evaluation status | TC-10, TC-11, TC-22 | API, Evaluation, Result |
| FR-13 | Display results | TC-10 | Web UI, Result Service |
| FR-14 | Evaluation errors | TC-11, TC-16 | API Error Handler |
| FR-15 | Download results | TC-12 | Result Service, Web UI |
| FR-16 | Prevent invalid evaluation | TC-07 | UI, API, Validation |
| FR-17 | Isolated temporary artifacts | TC-13, TC-18 | Storage |
| FR-18 | Evaluation metadata/ID | TC-22 | Result Service |
| FR-19 | Unknown evaluation ID | TC-24 | API, Result Service |
| FR-20 | Download before completion | TC-25 | API, Result Service |
| NFR-01 | Usability | TC-21 | Web UI |
| NFR-02 | 2-second acknowledgement | TC-19 | API |
| NFR-03 | Deterministic metrics | TC-20 | Metrics/Evaluation |
| NFR-04 | Reject unsupported files | TC-03 | Validation |
| NFR-05 | Safe errors | TC-16 | API Error Handler |
| NFR-06 | Upload limits | TC-04 | Security Policy |
| NFR-07 | Authentication when enabled | TC-17 | Authentication Middleware |
| NFR-08 | Traceable status | TC-10, TC-22 | Result Service |
| NFR-09 | Modular architecture | Architecture Review; automated check `backend/tests/test_architecture.py` | Layered Components |
| NFR-10 | Security validation | TC-03, TC-04, TC-13–TC-18, TC-23 | Security Policy, Validation |
| SEC-01 | File/type/size validation | TC-03, TC-04 | Validation |
| SEC-02 | Controlled storage path | TC-13 | Temporary Storage |
| SEC-03 | Reject malformed artifacts | TC-14, TC-23 | Validation |
| SEC-04 | Resource limits | TC-15 | Evaluation + Security Policy |
| SEC-05 | No sensitive error disclosure | TC-16 | API Error Handler |
| SEC-06 | Authentication | TC-17 | Authentication Middleware |
| SEC-07 | Temporary cleanup | TC-18 | Storage Lifecycle Manager |
| SEC-08 | Server-side input validation | TC-05, TC-06 | API + Validation |

Test execution results are in the [Test Report](../planning/Test_Report.md). Which automated tests cover each case is recorded in `backend/tests/traceability.py`, and `python scripts/tc_report.py` (run from `backend/`) regenerates the per-case result table.

---

## 8. Detailed Test Cases

| ID | Requirement(s) | Type | Preconditions | Test Data | Test Steps | Expected Result |
|---|---|---|---|---|---|---|
| TC-01 | FR-01 | Functional | Application is running | Reference classification model (`backend/tests/fixtures/classification/model.joblib`) | Choose a supported model file (`.joblib` or `.pkl`) in the Upload step, or send it to `POST /api/evaluations` | Model is accepted and shown as ready for evaluation (the API answers `202`) |
| TC-02 | FR-02 | Functional | Application is running | Valid classification dataset (`classification/data.csv`) | Upload a valid CSV dataset | Dataset is accepted and its available columns are shown (the Configure step lists the CSV header) |
| TC-03 | FR-03, FR-04, NFR-04, NFR-10, SEC-01 | Security/Functional | Application is running | Unsupported file (e.g. `.exe`) | Upload an unsupported file type (the browser blocks it before sending; the server check is tested through the API) | File is rejected before evaluation with `415 UNSUPPORTED_FILE_TYPE` and a clear message; nothing is stored and no evaluation is created |
| TC-04 | FR-03, FR-04, NFR-06, NFR-10, SEC-01 | Boundary/Security | Upload limit is configured (default 10 MB, `MLEVAL_MAX_UPLOAD_BYTES`) | Files exactly at and one byte above the configured size limit | Upload the file at the limit, then the file one byte above it | The file at the limit is accepted; the file one byte above is rejected with `413 FILE_TOO_LARGE` and a clear size-limit error, and no evaluation is created |
| TC-05 | FR-05, FR-07, SEC-08 | Functional/Security | Valid dataset uploaded | Missing-target dataset | Submit a target column that does not exist in the dataset (e.g. through the API) | Configuration is rejected with `422 INVALID_TARGET_COLUMN` and evaluation cannot start |
| TC-06 | FR-06, SEC-08 | Functional/Security | Valid inputs uploaded | Invalid task type (e.g. `clustering`) | Submit an unsupported/invalid task type through the API | Server rejects the request with `422 INVALID_TASK_TYPE` |
| TC-07 | FR-16 | Functional | Application is running | None (empty submission) | Try to evaluate without the model, dataset or configuration (the Next button stays disabled), and send an incomplete request to the API | Evaluation does not start; the API answers `400 MISSING_REQUIRED_FIELD` naming each missing field |
| TC-08 | FR-05, FR-06, FR-08, FR-09, FR-10 | Functional | Valid classification model/dataset | Deterministic classification pair with known expected metrics (`classification/` fixtures and `expected_metrics.json`) | Select classification and the target column, then run evaluation | Evaluation completes and accuracy, precision, recall and F1 are reported where applicable and match the expected values |
| TC-09 | FR-05, FR-06, FR-08, FR-09, FR-11 | Functional | Valid regression model/dataset | Deterministic regression pair with known expected metrics (`regression/` fixtures and `expected_metrics.json`) | Select regression and the target column, then run evaluation | Evaluation completes and MAE, MSE, RMSE and R² are reported and match the expected values |
| TC-10 | FR-12, FR-13, NFR-08 | Functional | Valid evaluation submitted | Valid classification model/dataset | Observe the status (poll `GET /api/evaluations/{id}`) and the completed result | Status moves `pending`, `running`, then `completed`, and the result is displayed |
| TC-11 | FR-08, FR-12, FR-14 | Negative | Evaluation is configured to fail, e.g. incompatible input | Incompatible model/dataset pair (`classification/model.joblib` with `negative/incompatible.csv`), and a dataset with the wrong target column chosen | Run evaluation | Status becomes `failed` with error code `INCOMPATIBLE_INPUTS` and a safe message that names the missing and unused columns |
| TC-12 | FR-15 | Functional | Evaluation completed | Completed evaluation (e.g. from TC-08) | Click **Download Results** on the results screen (shown once the evaluation has completed), or request `GET /api/evaluations/{id}/download` | A JSON file is returned as an attachment (`evaluation-<id>.json`) with the ID, task type, target column, input filenames, metrics and timestamps |
| TC-13 | FR-17, NFR-10, SEC-02 | Security | Upload endpoint available | File with a path-like filename such as `../../evil.csv` | Upload file with path-like/malicious filename | Server stores it under a random UUID name inside the storage directory and does not write outside it |
| TC-14 | FR-04, NFR-10, SEC-03 | Security | Upload endpoint available | Malformed model file (`negative/malformed_model.joblib`, and files that unpickle to something without `predict`) | Submit malformed model artifact | Artifact is rejected with `422 INVALID_MODEL` before it is used for evaluation, and a clear validation error is shown |
| TC-15 | NFR-10, SEC-04 | Security | Resource limits configured (time limit 60 s by default, `MLEVAL_EVALUATION_TIMEOUT_SECONDS`; memory limit 2 GiB by default, `MLEVAL_EVALUATION_MEMORY_LIMIT_BYTES`, enforced on Linux, macOS and Windows) | A model that runs longer than the time limit; a model that allocates more memory than the memory limit | Submit an evaluation exceeding configured resource/time limits | The evaluation ends `failed` with `RESOURCE_LIMIT_EXCEEDED` and a message naming the limit; the child process is killed |
| TC-16 | FR-04, FR-14, NFR-05, NFR-10, SEC-05 | Security | Application is running | Malformed CSV; incompatible model/dataset pair | Trigger a server-side validation error and a runtime evaluation error; inspect each API response | Each response contains a safe error code/message and no raw trace, secret, or server path; the same holds for unknown URLs and unexpected server errors |
| TC-17 | NFR-07, NFR-10, SEC-06 | Security | Authentication is enabled (`MLEVAL_AUTH_ENABLED=true` and `MLEVAL_API_KEY` set) | Request without credentials | Call `POST /api/evaluations`, `GET /api/evaluations/{id}` and `GET /api/evaluations/{id}/download` without credentials; then repeat with the key in `X-API-Key` or `Authorization: Bearer` | Requests without credentials are rejected with `401 UNAUTHENTICATED`; requests with the key succeed; `/api/health` stays open; if authentication is enabled with no key configured, every protected request is rejected |
| TC-18 | FR-17, NFR-10, SEC-07 | Security | Retention period configured (`MLEVAL_RETENTION_SECONDS`, 3600 s by default) | Completed evaluation | Complete an evaluation, wait longer than the retention period, and inspect the storage directory (the cleanup runs at start-up, every `MLEVAL_CLEANUP_INTERVAL_SECONDS` (300 s by default) and after each submission) | Artifacts older than the retention period are deleted without waiting for a new request, newer ones are kept, and the files of an evaluation that is still pending or running are kept whatever their age |
| TC-19 | NFR-02 | Performance | Valid evaluation endpoint available | Valid classification model/dataset | Send 10 valid evaluation requests one after another, one second apart (the pace of one user), and measure the time to the `202` (`backend/scripts/measure_ack_time.py`); the back-to-back time is also measured and reported | Each acknowledgement meets the defined 2-second target under normal local conditions |
| TC-20 | FR-09, NFR-03 | Non-functional | Deterministic reference model/dataset available | Deterministic model/dataset pair with known expected metrics | Run the identical evaluation three times (`backend/tests/test_determinism.py`) | Metric outputs are identical, subject to documented model nondeterminism |
| TC-21 | NFR-01 | Usability | Fresh test user | Valid classification model/dataset | Ask the user to perform upload → configure → evaluate → inspect result with no help; record whether each control was found (procedure and record sheet: `deliverable-1/usability-testing/`) | User can identify primary controls without developer assistance |
| TC-22 | FR-12, FR-18, NFR-08 | Functional | Valid evaluation submitted | Valid classification model/dataset | Inspect evaluation identifier and terminal state | Evaluation has a unique random identifier (UUID) and reaches `completed` or `failed`, and a terminal status never changes |
| TC-23 | FR-04, NFR-10, SEC-03 | Security/Negative | Application is running | Malformed CSV | Submit the malformed CSV with a valid model and configuration | Dataset is rejected with `422 MALFORMED_DATASET` before model execution and a clear validation error is shown |
| TC-24 | FR-19 | Negative | Application is running | Unknown evaluation identifier | Request the status/result and the download for the unknown identifier | Each request returns `404 EVALUATION_NOT_FOUND` |
| TC-25 | FR-20 | Negative | Evaluation submitted and not yet completed | Pending or running evaluation | Request the result download before the evaluation completes | Download is rejected with `409 EVALUATION_NOT_COMPLETED` and no result file is returned |

---

---

## 9. Automated Test Mapping

Each case above is covered by the automated tests listed here (generated from `backend/tests/traceability.py`, which `tests/test_traceability.py` checks against the real tests). Results are in the [System Validation Report](../docs/System_Validation_Report.md).

| Case | Automated tests (`backend/tests/`) |
|---|---|
| TC-01 | `test_api_submit.py::test_valid_classification_submission_is_accepted_with_an_id` |
| TC-02 | `test_api_submit.py::test_valid_classification_submission_is_accepted_with_an_id`<br>`test_api_submit.py::test_valid_regression_submission_is_accepted` |
| TC-03 | `test_api_submit.py::test_unsupported_file_type_is_rejected_and_creates_nothing` |
| TC-04 | `test_api_submit.py::test_model_exactly_at_size_limit_is_accepted`<br>`test_api_submit.py::test_model_one_byte_over_size_limit_is_rejected`<br>`test_api_submit.py::test_dataset_exactly_at_size_limit_is_accepted`<br>`test_api_submit.py::test_dataset_one_byte_over_size_limit_is_rejected`<br>`test_api_submit.py::test_enforce_file_size_stops_early_without_reading_entire_file` |
| TC-05 | `test_api_submit.py::test_target_column_not_in_dataset_is_rejected`<br>`test_api_submit.py::test_valid_target_column_in_dataset_is_accepted` |
| TC-06 | `test_api_submit.py::test_invalid_task_type_is_rejected` |
| TC-07 | `test_api_submit.py::test_missing_field_is_rejected_and_creates_nothing` |
| TC-08 | `test_acceptance.py::test_classification_reference_pair_reports_the_expected_metrics`<br>`test_metrics_service.py::test_classification_metrics_match_en02_reference_fixture` |
| TC-09 | `test_acceptance.py::test_regression_reference_pair_reports_the_expected_metrics`<br>`test_metrics_service.py::test_regression_metrics_match_en02_reference_fixture` |
| TC-10 | `test_api_status.py::test_status_follows_the_lifecycle_to_completed`<br>`test_api_status.py::test_end_to_end_submit_then_read_the_result` |
| TC-11 | `test_evaluation_limits.py::test_feature_mismatch_ends_as_incompatible_inputs`<br>`test_evaluation_limits.py::test_api_reports_incompatible_inputs_to_the_client`<br>`test_api_status.py::test_end_to_end_incompatible_inputs_end_failed_without_leaking_details` |
| TC-12 | `test_api_download.py::test_completed_evaluation_downloads_as_a_json_attachment`<br>`test_api_download.py::test_downloaded_metrics_match_the_reference_values` |
| TC-13 | `test_api_submit.py::test_client_filenames_never_reach_the_filesystem`<br>`test_storage.py::test_user_controlled_extensions_cannot_alter_the_path`<br>`test_storage.py::test_delete_removes_stored_file_but_not_outside_files` |
| TC-14 | `test_api_submit.py::test_malformed_model_is_rejected` |
| TC-15 | `test_evaluation_limits.py::test_exceeding_the_time_limit_stops_the_evaluation`<br>`test_evaluation_limits.py::test_api_stops_an_evaluation_that_exceeds_the_time_limit`<br>`test_evaluation_limits.py::test_exceeding_the_memory_limit_stops_the_evaluation`<br>`test_memory_limit.py::test_a_model_over_the_limit_is_stopped_on_windows` |
| TC-16 | `test_api_submit.py::test_error_responses_use_the_standard_format_without_internal_details`<br>`test_evaluation_limits.py::test_a_crashing_model_fails_with_a_generic_message_and_logs_the_traceback`<br>`test_api_status.py::test_end_to_end_incompatible_inputs_end_failed_without_leaking_details`<br>`test_errors.py::test_tc16_server_validation_error_leaks_no_trace_or_path`<br>`test_errors.py::test_tc16_runtime_evaluation_error_leaks_no_trace_or_path` |
| TC-17 | `test_auth.py::test_missing_credentials_rejected_with_401`<br>`test_auth.py::test_invalid_and_missing_credentials_return_401_for_both_get_and_post`<br>`test_auth.py::test_valid_x_api_key_header_post`<br>`test_auth.py::test_valid_authorization_bearer_header_post`<br>`test_auth.py::test_fail_secure_when_auth_enabled_but_no_key_configured`<br>`test_auth.py::test_download_endpoint_is_protected_and_works_with_credentials`<br>`test_auth.py::test_health_endpoint_remains_unauthenticated_when_auth_enabled` |
| TC-18 | `test_storage.py::test_cleanup_expired_deletes_files_older_than_retention_period`<br>`test_storage.py::test_cleanup_expired_boundary_exact_limit`<br>`test_storage.py::test_cleanup_expired_never_deletes_active_paths_even_if_expired`<br>`test_storage.py::test_api_background_retention_cleanup_e2e`<br>`test_retention.py::test_the_sweep_keeps_the_files_of_a_running_evaluation_and_removes_finished_ones`<br>`test_retention.py::test_expired_files_are_removed_at_start_up_without_any_request`<br>`test_retention.py::test_expired_files_are_removed_on_a_timer_without_any_request` |
| TC-19 | `test_ack_time.py::test_ten_valid_requests_are_each_acknowledged_within_two_seconds` |
| TC-20 | `test_determinism.py::test_repeated_evaluations_produce_identical_metrics` |
| TC-21 | Manual: Manual usability test with a fresh user (US-22); see deliverable-1/usability-testing/. |
| TC-22 | `test_result_service.py::test_create_stores_a_pending_record_with_a_random_uuid`<br>`test_result_service.py::test_ids_are_unique`<br>`test_result_service.py::test_a_terminal_status_never_changes`<br>`test_api_submit.py::test_each_submission_gets_a_different_id` |
| TC-23 | `test_api_submit.py::test_malformed_csv_is_rejected` |
| TC-24 | `test_api_status.py::test_unknown_id_is_a_404_with_the_standard_error`<br>`test_api_download.py::test_unknown_id_is_a_404` |
| TC-25 | `test_api_download.py::test_download_before_completion_is_a_409_with_no_file`<br>`test_api_download.py::test_failed_evaluation_has_nothing_to_download` |
