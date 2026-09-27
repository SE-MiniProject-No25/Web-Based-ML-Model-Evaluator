# Software Test Plan
## Web-Based ML Model Evaluator


## 1. Introduction

### 1.1 Purpose

This Test Plan defines the verification and validation approach for the Web-Based ML Model Evaluator. It covers functional behavior, non-functional properties, security validation, and traceability to the Software Requirements Specification.

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

- valid classification dataset;
- valid regression dataset;
- missing-target dataset;
- malformed CSV;
- unsupported file;
- oversized file;
- invalid task type;
- deterministic model/dataset pair with known expected metrics.

---

## 3. Test Cases and Test Procedures

The detailed cases are maintained in `04_Test_Cases.md`.

Each test case specifies:

- test ID;
- related requirement(s);
- preconditions;
- test data;
- steps;
- expected result;
- pass/fail criterion.

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
- unavailable result identifier.

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

A representative user shall attempt the primary workflow without developer assistance. The evaluator shall record whether upload, configuration, run, status, result, and download controls are identifiable.

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
| FR-04 | Validation errors | TC-03, TC-05, TC-16 | Validation, API Error Handler |
| FR-05 | Target selection | TC-05 | Web UI, Validation |
| FR-06 | Task selection | TC-06, TC-08, TC-09 | Web UI, Validation |
| FR-07 | Target exists | TC-05 | Validation |
| FR-08 | Execute model | TC-08, TC-09, TC-11 | Evaluation Service |
| FR-09 | Calculate metrics | TC-08, TC-09, TC-20 | Metrics Service |
| FR-10 | Classification metrics | TC-08 | Metrics Service |
| FR-11 | Regression metrics | TC-09 | Metrics Service |
| FR-12 | Evaluation status | TC-10, TC-22 | API, Evaluation, Result |
| FR-13 | Display results | TC-10 | Web UI, Result Service |
| FR-14 | Evaluation errors | TC-11, TC-16 | API Error Handler |
| FR-15 | Download results | TC-12 | Result Service, Web UI |
| FR-16 | Prevent invalid evaluation | TC-07 | UI, API, Validation |
| FR-17 | Isolated temporary artifacts | TC-13, TC-18 | Storage |
| FR-18 | Evaluation metadata/ID | TC-22 | Result Service |
| NFR-01 | Usability | TC-21 | Web UI |
| NFR-02 | 2-second acknowledgement | TC-19 | API |
| NFR-03 | Deterministic metrics | TC-20 | Metrics/Evaluation |
| NFR-04 | Reject unsupported files | TC-03 | Validation |
| NFR-05 | Safe errors | TC-16 | API Error Handler |
| NFR-06 | Upload limits | TC-04 | Security Policy |
| NFR-07 | Authentication when enabled | TC-17 | Auth Middleware |
| NFR-08 | Traceable status | TC-10, TC-22 | Result Service |
| NFR-09 | Modular architecture | Architecture Review | Layered Components |
| NFR-10 | Security validation | TC-03, TC-04, TC-13–TC-18 | Security Policy, Validation |
| SEC-01 | File/type/size validation | TC-03, TC-04 | Validation |
| SEC-02 | Controlled storage path | TC-13 | Temporary Storage |
| SEC-03 | Reject malformed artifacts | TC-14 | Validation |
| SEC-04 | Resource limits | TC-15 | Evaluation + Security Policy |
| SEC-05 | No sensitive error disclosure | TC-16 | API Error Handler |
| SEC-06 | Authentication | TC-17 | Auth Middleware |
| SEC-07 | Temporary cleanup | TC-18 | Storage Lifecycle |
| SEC-08 | Server-side input validation | TC-05, TC-06 | API + Validation |

---

## 8. Detailed Test Cases

| ID | Requirement(s) | Type | Preconditions | Test Steps | Expected Result |
|---|---|---|---|---|---|
| TC-01 | FR-01 | Functional | Application is running | Upload a supported model file | Model is accepted and shown as ready for evaluation |
| TC-02 | FR-02 | Functional | Application is running | Upload a valid CSV dataset | Dataset is accepted and its available columns are shown |
| TC-03 | FR-03, SEC-01 | Security/Functional | Application is running | Upload an unsupported file type | File is rejected before evaluation and a clear validation error is shown |
| TC-04 | FR-03, NFR-06, SEC-01 | Boundary/Security | Upload limit is configured | Upload a file larger than the configured maximum | Upload is rejected and evaluation does not start |
| TC-05 | FR-05, FR-07, SEC-08 | Functional/Security | Valid dataset uploaded | Select a target column that does not exist | Configuration is rejected and evaluation cannot start |
| TC-06 | FR-06, SEC-08 | Functional/Security | Valid inputs uploaded | Submit an unsupported/invalid task type through the API | Server rejects the request with a defined validation error |
| TC-07 | FR-16 | Functional | Application is running | Click Evaluate without required model/dataset/configuration | Evaluation does not start and missing inputs are identified |
| TC-08 | FR-08, FR-09, FR-10 | Functional | Valid classification model/dataset | Select classification and run evaluation | Evaluation completes and accuracy, precision, recall and F1 are reported where applicable |
| TC-09 | FR-08, FR-11 | Functional | Valid regression model/dataset | Select regression and run evaluation | Evaluation completes and MAE, MSE, RMSE and R² are reported |
| TC-10 | FR-12, FR-13 | Functional | Valid evaluation submitted | Observe status and completed result | Status transitions through the defined lifecycle and result is displayed |
| TC-11 | FR-14 | Negative | Evaluation is configured to fail, e.g. incompatible input | Run evaluation | Status becomes failed and a safe, user-readable error is shown |
| TC-12 | FR-15 | Functional | Evaluation completed | Select Download Result | Structured result file is returned/downloaded |
| TC-13 | FR-17, SEC-02 | Security | Upload endpoint available | Upload file with path-like/malicious filename | Server uses a controlled storage name/path and does not write outside allowed storage |
| TC-14 | SEC-03 | Security | Upload endpoint available | Submit malformed model artifact | Artifact is rejected before model execution |
| TC-15 | SEC-04 | Security | Resource limits configured | Submit an evaluation exceeding configured resource/time limits | Request is stopped/rejected according to the configured policy |
| TC-16 | SEC-05, NFR-05 | Security | Trigger a server-side validation/runtime error | Inspect API response | Response contains safe error code/message and no raw trace, secret, or server path |
| TC-17 | SEC-06, NFR-07 | Security | Authentication is enabled | Call protected evaluation/result endpoint without credentials | Request is rejected as unauthenticated |
| TC-18 | SEC-07 | Security | Evaluation lifecycle completed | Inspect temporary storage according to policy | Temporary artifacts are removed according to configured retention policy |
| TC-19 | NFR-02 | Performance | Valid evaluation endpoint available | Send 10 valid evaluation requests and measure acknowledgement time | Each acknowledgement meets the defined 2-second target under normal local conditions |
| TC-20 | NFR-03 | Non-functional | Deterministic reference model/dataset available | Run identical evaluation three times | Metric outputs are identical, subject to documented model nondeterminism |
| TC-21 | NFR-01 | Usability | Fresh test user | Ask user to perform upload → configure → evaluate → inspect result | User can identify primary controls without developer assistance |
| TC-22 | NFR-08, FR-18 | Functional | Valid evaluation submitted | Inspect evaluation identifier and terminal state | Evaluation has a unique identifier and reaches completed or failed status |

---