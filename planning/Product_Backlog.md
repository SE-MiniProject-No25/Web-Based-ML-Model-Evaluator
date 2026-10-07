# Product Backlog
## Web-Based ML Model Evaluator

Every Functional (FR) and Non-Functional (NFR) requirement in the [SRS](../deliverable-1/01_SRS.md) is covered by at least one backlog item below, and every test case in the [Test Plan](../deliverable-1/02_Test_Plan.md) is owned by one. Sprint dates, roles and workflow are in the [Sprint Plan](Sprint_Plan.md).

Estimates are story points (1, 2, 3, 5, 8): relative effort, not hours.

## 1. Backlog Overview

| ID | Item | Type | Owner | Sprint | Pts | Requirements |
|---|---|---|---|---|---|---|
| EN-01 | Project skeleton, tech stack and CI | enabler | Adyanth | 1 | 3 | NFR-09 |
| EN-02 | Reference test fixtures (models + datasets with known metrics) | enabler | Akshya Sivagami | 1 | 3 | FR-09, FR-10, FR-11, NFR-03 |
| EN-04 | Enforce component separation (NFR-09) | enabler | Adyanth | 1 | 1 | NFR-09 |
| EN-05 | Result Service: store and retrieve evaluations | enabler | Adyanth | 1 | 2 | FR-18, NFR-08 |
| EN-06 | Evaluation runner: load model, predict, hand off to metrics | enabler | Adyanth | 1 | 3 | FR-08, FR-12 |
| US-01 | Submit an evaluation (POST /api/evaluations) | user-story | Adyanth | 1 | 3 | FR-01, FR-02, FR-12 |
| US-02 | Check status and results (GET /api/evaluations/{id}) | user-story | Adyanth | 1 | 3 | FR-12, FR-13, FR-19 |
| US-06 | Reject unsupported and oversized files | user-story | Akash MP | 1 | 5 | FR-03, FR-04, NFR-04, NFR-06, NFR-10, SEC-01 |
| US-07 | Reject malformed datasets and models | user-story | Akash MP | 1 | 3 | FR-04, NFR-10, SEC-03 |
| US-08 | Validate the evaluation configuration on the server | user-story | Akash MP | 1 | 3 | FR-07, FR-16, SEC-08 |
| US-12 | Upload a model and dataset in the browser | user-story | Akshath Patil | 1 | 3 | FR-01, FR-02 |
| US-13 | Configure the evaluation | user-story | Akshath Patil | 1 | 3 | FR-05, FR-06, FR-16 |
| US-14 | Run an evaluation and watch its status | user-story | Akshath Patil | 1 | 3 | FR-12 |
| US-19 | Compute classification metrics | user-story | Akshya Sivagami | 1 | 3 | FR-09, FR-10 |
| US-20 | Compute regression metrics | user-story | Akshya Sivagami | 1 | 2 | FR-09, FR-11 |
| EN-03 | Integration, full test run and Test Report | enabler | Adyanth | 2 | 2 | All FR/NFR/SEC (Test Plan §4.3 and §7) |
| EN-07 | API documentation that matches the Architecture contract | enabler | Adyanth | 2 | 2 | SRS §3.3.2 (API Interface) |
| EN-08 | Demo script and rehearsal | enabler | Adyanth | 2 | 1 | UC-01, UC-02, UC-03 |
| US-03 | Download results (GET /api/evaluations/{id}/download) | user-story | Adyanth | 2 | 3 | FR-15, FR-19, FR-20 |
| US-04 | Handle failed evaluations and resource limits | user-story | Adyanth | 2 | 5 | FR-14, NFR-08, SEC-04 |
| US-05 | Meet the 2-second acknowledgement target | test | Adyanth | 2 | 2 | NFR-02 |
| US-09 | Safe, consistent error responses | user-story | Akash MP | 2 | 3 | FR-04, FR-14, NFR-05, NFR-10, SEC-05 |
| US-10 | Secure temporary storage and cleanup | user-story | Akash MP | 2 | 5 | FR-17, NFR-10, SEC-02, SEC-07 |
| US-11 | Optional authentication for the API | user-story | Akash MP | 2 | 3 | NFR-07, SEC-06 |
| US-15 | View results as a table and chart | user-story | Akshath Patil | 2 | 3 | FR-10, FR-11, FR-13 |
| US-16 | Show validation and evaluation errors clearly | user-story | Akshath Patil | 2 | 2 | FR-04, FR-14 |
| US-17 | Download results from the UI | user-story | Akshath Patil | 2 | 1 | FR-15 |
| US-18 | Make the workflow easy to follow | user-story | Akshath Patil | 2 | 2 | NFR-01 |
| US-21 | Prove metrics are deterministic | test | Akshya Sivagami | 2 | 1 | NFR-03 |
| US-22 | Run the usability test | test | Akshya Sivagami | 2 | 1 | NFR-01 |

**Total:** 79 points — Sprint 1: 43, Sprint 2: 36.

## 2. Requirement Coverage

### 2.1 Functional Requirements

| Requirement | Backlog items |
|---|---|
| FR-01 | US-01, US-12 |
| FR-02 | US-01, US-12 |
| FR-03 | US-06 |
| FR-04 | US-06, US-07, US-09, US-16 |
| FR-05 | US-13 |
| FR-06 | US-13 |
| FR-07 | US-08 |
| FR-08 | EN-06 |
| FR-09 | EN-02, US-19, US-20 |
| FR-10 | EN-02, US-15, US-19 |
| FR-11 | EN-02, US-15, US-20 |
| FR-12 | EN-06, US-01, US-02, US-14 |
| FR-13 | US-02, US-15 |
| FR-14 | US-04, US-09, US-16 |
| FR-15 | US-03, US-17 |
| FR-16 | US-08, US-13 |
| FR-17 | US-10 |
| FR-18 | EN-05 |
| FR-19 | US-02, US-03 |
| FR-20 | US-03 |

### 2.2 Non-Functional Requirements

| Requirement | Backlog items |
|---|---|
| NFR-01 | US-18, US-22 |
| NFR-02 | US-05 |
| NFR-03 | EN-02, US-21 |
| NFR-04 | US-06 |
| NFR-05 | US-09 |
| NFR-06 | US-06 |
| NFR-07 | US-11 |
| NFR-08 | EN-05, US-04 |
| NFR-09 | EN-01, EN-04 |
| NFR-10 | US-06, US-07, US-09, US-10 |

### 2.3 Test Cases

| Test case | Backlog items |
|---|---|
| TC-01 | US-01, US-12 (full run: EN-03) |
| TC-02 | US-01, US-12 (full run: EN-03) |
| TC-03 | EN-02, US-06 (full run: EN-03) |
| TC-04 | EN-02, US-06 (full run: EN-03) |
| TC-05 | US-08 (full run: EN-03) |
| TC-06 | US-08 (full run: EN-03) |
| TC-07 | US-08, US-13 (full run: EN-03) |
| TC-08 | EN-02, EN-06, US-15, US-19 (full run: EN-03) |
| TC-09 | EN-02, EN-06, US-15, US-20 (full run: EN-03) |
| TC-10 | EN-05, US-02, US-14 (full run: EN-03) |
| TC-11 | EN-02, EN-06, US-04, US-16 (full run: EN-03) |
| TC-12 | US-03, US-17 (full run: EN-03) |
| TC-13 | EN-02, US-10 (full run: EN-03) |
| TC-14 | EN-02, US-07 (full run: EN-03) |
| TC-15 | US-04 (full run: EN-03) |
| TC-16 | US-09, US-16 (full run: EN-03) |
| TC-17 | US-11 (full run: EN-03) |
| TC-18 | US-10 (full run: EN-03) |
| TC-19 | US-05 (full run: EN-03) |
| TC-20 | EN-02, US-21 (full run: EN-03) |
| TC-21 | US-18, US-22 (full run: EN-03) |
| TC-22 | EN-05 (full run: EN-03) |
| TC-23 | EN-02, US-07 (full run: EN-03) |
| TC-24 | US-02, US-03 (full run: EN-03) |
| TC-25 | US-03 (full run: EN-03) |

## 3. Backlog Items

### Sprint 1 (Wed 7 Oct – Tue 13 Oct 2026)

#### EN-01 — Project skeleton, tech stack and CI

**Owner:** Adyanth · **Points:** 3 · **Type:** enabler · **Area:** Setup / CI / Tooling

*As the team, we want a working repository skeleton with one module per architecture component and CI running on every pull request, so that all four of us can build in parallel from day one.*

Acceptance criteria:

- `backend/` has one package per component in Architecture §3: `api`, `validation`, `evaluation`, `metrics`, `results`, `storage`, `security` (NFR-09).
- Backend and frontend each start with one documented command; the README explains both.
- A shared error type and the `{"error": {"code", "message"}}` format (Architecture §10.4) exist, so every other story uses the same errors.
- A basic storage module saves uploads under server-generated (UUID) names in a temp directory outside the source tree; US-10 hardens it.
- One config file holds: allowed extensions, upload size limit, evaluation time limit, retention period, auth on/off.
- `.github/pull_request_template.md` asks for `Closes #<issue>`, the acceptance criteria covered and the test cases run.
- GitHub Actions runs lint + `pytest` on every PR; `main` requires a PR with 1 approving review.
- Supported model format is decided and written in the README (see Sprint Plan → Decisions).

Requirements: NFR-09 · Test cases: —

#### EN-02 — Reference test fixtures (models + datasets with known metrics)

**Owner:** Akshya Sivagami · **Points:** 3 · **Type:** enabler · **Area:** Testing & QA

*As a developer or tester, I want one shared set of reference models and datasets with known expected results, so that every test case in the Test Plan runs the same way for everyone.*

Acceptance criteria:

- A deterministic classification model + CSV, with expected accuracy / precision / recall / F1 saved in a JSON file.
- A deterministic regression model + CSV, with expected MAE / MSE / RMSE / R² saved the same way.
- Negative fixtures: unsupported file (e.g. `.exe`), malformed CSV, malformed model file, an incompatible model/dataset pair (wrong feature columns), and a path-like filename such as `../../evil.csv`.
- Size-limit files (exactly at and 1 byte over the limit) are generated by a test helper, not committed.
- A script regenerates all fixtures; everything lives under `backend/tests/fixtures/`.

Requirements: FR-09, FR-10, FR-11, NFR-03 · Test cases: TC-03, TC-04, TC-08, TC-09, TC-11, TC-13, TC-14, TC-20, TC-23

#### EN-04 — Enforce component separation (NFR-09)

**Owner:** Adyanth · **Points:** 1 · **Type:** enabler · **Area:** Setup / CI / Tooling

*As the team, we want the component boundaries from the Architecture document checked automatically, so that UI, API, validation, evaluation and result handling stay separate as the code grows.*

Acceptance criteria:

- The README has a short code map linking every backend package and frontend folder to its Architecture §3 component.
- A pytest test fails the build if a lower layer imports an upper one (e.g. `validation`, `evaluation`, `metrics` or `results` importing from `api`, or backend code importing frontend code).
- The check runs in the CI pipeline from EN-01.
- It is the evidence for the NFR-09 acceptance criterion: the architecture review identifies separate components/interfaces for UI, API, validation, evaluation and result handling.

Requirements: NFR-09 · Test cases: — · Depends on: EN-01

> The Test Plan §7 verifies NFR-09 by architecture review; this gives that review something concrete to check.

#### EN-05 — Result Service: store and retrieve evaluations

**Owner:** Adyanth · **Points:** 2 · **Type:** enabler · **Area:** Backend / API / Evaluation

*As the backend, we want one place that creates, updates and returns evaluation records, so that the API and the evaluation runner always agree on an evaluation's status and results.*

Acceptance criteria:

- `create()` stores a new record: random UUID, task type, target column, original filenames, created time, status `pending` (FR-18).
- The status moves only `pending` → `running` → `completed` or `failed`; `completed` stores the metrics, `failed` stores a safe error object (`code`, `message`), and a finished time is recorded. A terminal status can never change (NFR-08).
- `get(id)` returns the record, or a not-found result the API turns into `404 EVALUATION_NOT_FOUND`.
- The store sits behind a small interface (in-memory to start) and is safe for concurrent requests.
- Unit tests cover the lifecycle and the unknown-ID case; TC-22 passes through the API once US-01 is merged.

Requirements: FR-18, NFR-08 · Test cases: TC-10, TC-22 · Depends on: EN-01

> US-01, US-02, US-03 and the runner (EN-06) all build on this, so it is due early in Sprint 1.

#### EN-06 — Evaluation runner: load model, predict, hand off to metrics

**Owner:** Adyanth · **Points:** 3 · **Type:** enabler · **Area:** Backend / API / Evaluation

*As an evaluator, I want my model to be run on my dataset in the background, so that I get predictions scored without the page freezing.*

Acceptance criteria:

- The runner starts as a background task after the `202`, and sets the status to `running` through the Result Service.
- It loads the supported model file, removes the target column from the dataset, and predicts on the remaining columns (FR-08).
- It passes the predictions and the target values to the Metrics Service (`compute(task_type, y_true, y_pred)`) and stores the metrics with status `completed` (FR-12).
- Any exception ends the evaluation as `failed` with a generic safe error (the limits and detailed errors come in US-04).
- Works end to end with the classification and regression fixtures from EN-02.

Requirements: FR-08, FR-12 · Test cases: TC-08, TC-09, TC-11 · Depends on: EN-01, EN-05, EN-02

> Stub the metrics call until US-19/US-20 land.

#### US-01 — Submit an evaluation (POST /api/evaluations)

**Owner:** Adyanth · **Points:** 3 · **Type:** user-story · **Area:** Backend / API / Evaluation

*As an evaluator, I want to submit my model, dataset, task type and target column in one request and get an evaluation ID back straight away, so that I can follow the evaluation while it runs.*

Acceptance criteria:

- `POST /api/evaluations` (multipart: `model`, `dataset`, `task_type`, `target_column`) runs the Validation Service first; invalid input returns the Section 11 error and creates no evaluation.
- Valid input is saved through Temporary Storage, an evaluation record is created through the Result Service (EN-05), and the evaluation runner (EN-06) is started in the background.
- The response is `202` with `{"evaluation_id", "status": "pending"}`; the ID is a random UUID.
- TC-01 passes as an automated test.

Requirements: FR-01, FR-02, FR-12 · Test cases: TC-01, TC-02 · Depends on: EN-01, EN-05

> Stub the validator until US-06/07/08 land and the runner until EN-06 lands.

#### US-02 — Check status and results (GET /api/evaluations/{id})

**Owner:** Adyanth · **Points:** 3 · **Type:** user-story · **Area:** Backend / API / Evaluation

*As an evaluator, I want to ask for my evaluation's status and see the metrics once it is done, so that I know when my results are ready.*

Acceptance criteria:

- Returns the current status; `completed` responses include `task_type` and `metrics` exactly as in Architecture §10.2; `failed` responses include the `error` object instead.
- An unknown ID returns `404 EVALUATION_NOT_FOUND` (FR-19).
- TC-10 and the status half of TC-24 pass.

Requirements: FR-12, FR-13, FR-19 · Test cases: TC-10, TC-24 · Depends on: EN-05

#### US-06 — Reject unsupported and oversized files

**Owner:** Akash MP · **Points:** 5 · **Type:** user-story · **Area:** Validation & Security

*As an evaluator, I want a wrong or too-large file rejected immediately with a clear reason, so that I don't wait for an evaluation that could never work.*

Acceptance criteria:

- Model and dataset extensions/types are checked against the config allowlist → `415 UNSUPPORTED_FILE_TYPE`.
- The size limit is enforced while the upload is read (not after loading it all) → `413 FILE_TOO_LARGE`; a file exactly at the limit is accepted.
- Both checks happen before anything is stored or executed (NFR-04, SEC-01).
- TC-03 and TC-04 pass.

Requirements: FR-03, FR-04, NFR-04, NFR-06, NFR-10, SEC-01 · Test cases: TC-03, TC-04 · Depends on: EN-01

#### US-07 — Reject malformed datasets and models

**Owner:** Akash MP · **Points:** 3 · **Type:** user-story · **Area:** Validation & Security

*As an evaluator, I want a broken CSV or model file rejected before it runs, so that I get a clear message instead of a failed evaluation.*

Acceptance criteria:

- An unparseable, empty, header-less or ragged CSV → `422 MALFORMED_DATASET`.
- A model file that cannot be loaded, or has no `predict`, → `422 INVALID_MODEL`.
- Both happen before model execution (SEC-03); model loading for this check happens in the same isolated process as US-04.
- TC-14 and TC-23 pass.

Requirements: FR-04, NFR-10, SEC-03 · Test cases: TC-14, TC-23 · Depends on: EN-01

#### US-08 — Validate the evaluation configuration on the server

**Owner:** Akash MP · **Points:** 3 · **Type:** user-story · **Area:** Validation & Security

*As an evaluator, I want the server to check my task type and target column itself, so that a bad configuration can never start an evaluation, even if the UI is bypassed.*

Acceptance criteria:

- Any missing `model` / `dataset` / `task_type` / `target_column` → `400 MISSING_REQUIRED_FIELD`, listing the missing fields (FR-16).
- A task type other than `classification` / `regression` → `422 INVALID_TASK_TYPE` (SEC-08).
- A target column not in the CSV header → `422 INVALID_TARGET_COLUMN` (FR-07).
- These checks never rely on the UI having validated first.
- TC-05, TC-06 and the API half of TC-07 pass.

Requirements: FR-07, FR-16, SEC-08 · Test cases: TC-05, TC-06, TC-07 · Depends on: EN-01

#### US-12 — Upload a model and dataset in the browser

**Owner:** Akshath Patil · **Points:** 3 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want to pick my model and CSV in the browser and see that they're ready, so that I know my inputs were understood before I run anything.*

Acceptance criteria:

- Separate model and dataset pickers show the accepted extensions.
- Once a CSV is chosen, its column names are read from the header and shown (FR-02, TC-02).
- Chosen files show as ready with name and size (TC-01).
- A quick client-side extension/size check gives instant feedback (the server still validates).

Requirements: FR-01, FR-02 · Test cases: TC-01, TC-02 · Depends on: EN-01

#### US-13 — Configure the evaluation

**Owner:** Akshath Patil · **Points:** 3 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want to choose the task type and target column from lists, so that I can't make a typo and I know what's still missing.*

Acceptance criteria:

- Task-type dropdown: classification / regression (FR-06).
- Target-column dropdown filled from the dataset header (FR-05).
- The Evaluate button stays disabled until all four inputs are set, and missing ones are highlighted (FR-16, UI half of TC-07).

Requirements: FR-05, FR-06, FR-16 · Test cases: TC-07 · Depends on: US-12

#### US-14 — Run an evaluation and watch its status

**Owner:** Akshath Patil · **Points:** 3 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want to press Evaluate and watch the status change, so that I know the system is working and when it's done.*

Acceptance criteria:

- Evaluate sends the multipart request to `POST /api/evaluations` and shows the returned evaluation ID.
- The UI polls `GET /api/evaluations/{id}` about every second until `completed` or `failed`.
- A status badge shows pending / running / completed / failed (FR-12, TC-10).
- Built against a mock of the Architecture §10 contract until US-01/US-02 are merged.

Requirements: FR-12 · Test cases: TC-10 · Depends on: US-13

#### US-19 — Compute classification metrics

**Owner:** Akshya Sivagami · **Points:** 3 · **Type:** user-story · **Area:** Metrics

*As an evaluator, I want accuracy, precision, recall and F1 for my classifier, so that I can judge it with standard measures.*

Acceptance criteria:

- The Metrics Service exposes one function, e.g. `compute(task_type, y_true, y_pred) -> dict`.
- Accuracy is always reported; precision/recall/F1 use the positive class for binary targets and macro average for multiclass (documented in the code and README).
- Metrics that don't apply (e.g. only one class present) are left out instead of crashing.
- Results match the EN-02 expected values; unit tests cover binary and multiclass (TC-08).

Requirements: FR-09, FR-10 · Test cases: TC-08 · Depends on: EN-02

#### US-20 — Compute regression metrics

**Owner:** Akshya Sivagami · **Points:** 2 · **Type:** user-story · **Area:** Metrics

*As an evaluator, I want MAE, MSE, RMSE and R² for my regressor, so that I can judge its error.*

Acceptance criteria:

- The same `compute` function returns MAE, MSE, RMSE and R² for regression.
- A constant target (R² undefined) is handled without crashing.
- Results match the EN-02 expected values; unit tests pass (TC-09).

Requirements: FR-09, FR-11 · Test cases: TC-09 · Depends on: EN-02

### Sprint 2 (Wed 14 Oct – Tue 20 Oct 2026)

#### EN-03 — Integration, full test run and Test Report

**Owner:** Adyanth · **Points:** 2 · **Type:** enabler · **Area:** Testing & QA

*As the team, we want every Test Plan case executed and recorded, so that we can show each FR and NFR is met and demo with confidence.*

Acceptance criteria:

- All 25 test cases are run; pass/fail and evidence are recorded in a Test Report.
- Every test case that can be automated is automated in `pytest`; manual ones (e.g. TC-21) are written up.
- The Test Plan §4.3 exit criteria are checked off: all mandatory cases executed, security cases executed, traceability complete, unresolved defects documented with severity and status.
- The RTM and Test Plan are updated if any requirement or design detail changed during the sprints.

Requirements: All FR/NFR/SEC (Test Plan §4.3 and §7) · Test cases: TC-01..TC-25

#### EN-07 — API documentation that matches the Architecture contract

**Owner:** Adyanth · **Points:** 2 · **Type:** enabler · **Area:** Backend / API / Evaluation

*As a frontend developer and as a marker, I want the running API documented exactly as in the Architecture document, so that I can use it without reading the backend code.*

Acceptance criteria:

- The running app serves interactive OpenAPI docs at `/docs` listing every endpoint, request field, response and error code from Architecture §10–11.
- The README has a "Run and try it" section with `curl` examples for submit → status → download.
- Any difference between the implementation and Architecture §10/§11 is fixed in the code or in the document.
- The frontend can switch from its mock to the real API using only these docs.

Requirements: SRS §3.3.2 (API Interface) · Test cases: — · Depends on: US-03, US-09

> SRS §3.3.2 requires an API for uploading/validating artifacts, creating evaluations, querying status/results and downloading results; the contract is Architecture §10–11.

#### EN-08 — Demo script and rehearsal

**Owner:** Adyanth · **Points:** 1 · **Type:** enabler · **Area:** Testing & QA

*As the team, we want a short rehearsed demo, so that we can show every key requirement working without surprises.*

Acceptance criteria:

- A 5-minute script covers the happy path (UC-01), a download (UC-03), one validation rejection (UC-02), one failed evaluation and one security rejection.
- The demo data (from EN-02) and a clean environment are ready, with a backup recording or screenshots.
- The whole team rehearses it once and each person knows which part they present.

Requirements: UC-01, UC-02, UC-03 · Test cases: — · Depends on: EN-03

> The use cases are defined in SRS §5.

#### US-03 — Download results (GET /api/evaluations/{id}/download)

**Owner:** Adyanth · **Points:** 3 · **Type:** user-story · **Area:** Backend / API / Evaluation

*As an evaluator, I want to download my completed results as a file, so that I can keep them or put them in a report.*

Acceptance criteria:

- A completed evaluation downloads as a JSON file (`Content-Disposition: attachment`) containing the ID, task type, target column, input filenames, metrics and timestamps (FR-15).
- A pending or running evaluation returns `409 EVALUATION_NOT_COMPLETED` and no file (FR-20).
- An unknown ID returns `404 EVALUATION_NOT_FOUND` (FR-19).
- TC-12, the download half of TC-24, and TC-25 pass.

Requirements: FR-15, FR-19, FR-20 · Test cases: TC-12, TC-24, TC-25 · Depends on: US-02

#### US-04 — Handle failed evaluations and resource limits

**Owner:** Adyanth · **Points:** 5 · **Type:** user-story · **Area:** Backend / API / Evaluation

*As an evaluator, I want a failed evaluation to tell me what went wrong in plain words, and a runaway evaluation to be stopped, so that I am never left waiting or shown a crash.*

Acceptance criteria:

- A model/dataset feature mismatch ends as `failed` with `INCOMPATIBLE_INPUTS` (FR-14).
- Model execution runs in a separate process with the configured time limit (and memory limit where the OS supports it); exceeding it ends as `failed` with `RESOURCE_LIMIT_EXCEEDED` (SEC-04).
- Any other exception ends as `failed` with `EVALUATION_FAILED`; the full traceback is logged server-side only.
- TC-11 and TC-15 pass.

Requirements: FR-14, NFR-08, SEC-04 · Test cases: TC-11, TC-15 · Depends on: EN-06

#### US-05 — Meet the 2-second acknowledgement target

**Owner:** Adyanth · **Points:** 2 · **Type:** test · **Area:** Backend / API / Evaluation

*As an evaluator, I want the app to accept my evaluation within 2 seconds, so that it feels responsive even when the evaluation itself takes longer.*

Acceptance criteria:

- A script sends 10 valid evaluation requests to a local deployment and records each acknowledgement time.
- All 10 are under 2 seconds; the numbers go into the Test Report.
- Nothing slow (model execution, metrics) runs before the `202` is returned.

Requirements: NFR-02 · Test cases: TC-19 · Depends on: US-01

#### US-09 — Safe, consistent error responses

**Owner:** Akash MP · **Points:** 3 · **Type:** user-story · **Area:** Validation & Security

*As an evaluator, I want every error to be a short, readable message and never a stack trace, so that I know what to fix and the server's internals stay private.*

Acceptance criteria:

- One global handler turns every error in Architecture §11 into `{"error": {"code", "message"}}` with the listed HTTP status.
- Unexpected exceptions return a generic `500` message; no traceback, file path or secret ever reaches the client (NFR-05, SEC-05).
- A test sends every error case and asserts no response contains `Traceback`, a server path or a config value.
- TC-16 passes.

Requirements: FR-04, FR-14, NFR-05, NFR-10, SEC-05 · Test cases: TC-16 · Depends on: US-06, US-07, US-08

#### US-10 — Secure temporary storage and cleanup

**Owner:** Akash MP · **Points:** 5 · **Type:** user-story · **Area:** Validation & Security

*As the operator, I want uploads kept in an isolated temp area under server-chosen names and deleted after use, so that users can't overwrite app files and old uploads don't pile up.*

Acceptance criteria:

- Uploads are saved as `<uuid>.<ext>` in a dedicated temp directory outside the source/config tree; the user's filename is kept only as metadata (FR-17, SEC-02).
- A path-like filename (e.g. `../../app/main.py`) cannot write outside the temp directory (TC-13).
- The temp directory is readable/writable only by the app user.
- Artifacts are deleted when the evaluation lifecycle ends, per the configured retention period (SEC-07, TC-18).

Requirements: FR-17, NFR-10, SEC-02, SEC-07 · Test cases: TC-13, TC-18 · Depends on: EN-01

#### US-11 — Optional authentication for the API

**Owner:** Akash MP · **Points:** 3 · **Type:** user-story · **Area:** Validation & Security

*As the operator, I want to be able to switch on authentication, so that only people with the key can run evaluations or read results.*

Acceptance criteria:

- `AUTH_ENABLED` config flag (default off); the API key comes from an environment variable and is never committed.
- When enabled, every `/api/evaluations` endpoint needs the key; missing or wrong → `401 UNAUTHENTICATED`.
- When disabled, the endpoints work without credentials.
- TC-17 passes.

Requirements: NFR-07, SEC-06 · Test cases: TC-17 · Depends on: US-01

#### US-15 — View results as a table and chart

**Owner:** Akshath Patil · **Points:** 3 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want my metrics shown as a clear table and chart, so that I can read my model's performance at a glance.*

Acceptance criteria:

- Classification shows accuracy, precision, recall, F1; regression shows MAE, MSE, RMSE, R² (only the metrics the API returns).
- Values are shown to 4 decimal places in a table, plus a simple bar chart (FR-13).
- The screen values match the expected values from EN-02 for TC-08 and TC-09.

Requirements: FR-10, FR-11, FR-13 · Test cases: TC-08, TC-09 · Depends on: US-14

#### US-16 — Show validation and evaluation errors clearly

**Owner:** Akshath Patil · **Points:** 2 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want errors shown next to the thing I need to fix, so that I can correct it without guessing.*

Acceptance criteria:

- API errors (400/401/404/409/413/415/422) show the server's message next to the relevant control (FR-04).
- A failed evaluation shows its error message in the results area (FR-14, UI half of TC-11).
- A network failure shows a friendly retry message instead of a blank screen.

Requirements: FR-04, FR-14 · Test cases: TC-11, TC-16 · Depends on: US-14

#### US-17 — Download results from the UI

**Owner:** Akshath Patil · **Points:** 1 · **Type:** user-story · **Area:** Web UI

*As an evaluator, I want a Download button once my results are ready, so that I can save them in one click.*

Acceptance criteria:

- The button appears/enables only when the status is `completed`.
- Clicking it downloads the file from `GET /api/evaluations/{id}/download` (UI half of TC-12).

Requirements: FR-15 · Test cases: TC-12 · Depends on: US-15

#### US-18 — Make the workflow easy to follow

**Owner:** Akshath Patil · **Points:** 2 · **Type:** user-story · **Area:** Web UI

*As a first-time user, I want the page to lead me through the steps, so that I can evaluate a model without instructions.*

Acceptance criteria:

- The page is laid out as four labelled steps: Upload → Configure → Run → Results, covering every control in SRS §3.3.1.
- The layout works on a normal laptop screen and a narrow window.
- Issues found in the US-22 usability test are fixed or logged.

Requirements: NFR-01 · Test cases: TC-21 · Depends on: US-15

#### US-21 — Prove metrics are deterministic

**Owner:** Akshya Sivagami · **Points:** 1 · **Type:** test · **Area:** Testing & QA

*As an evaluator, I want the same inputs to always give the same numbers, so that I can trust and repeat my results.*

Acceptance criteria:

- An automated test runs the same evaluation three times through the API and asserts identical metrics (TC-20).

Requirements: NFR-03 · Test cases: TC-20 · Depends on: US-01, US-19, US-20

#### US-22 — Run the usability test

**Owner:** Akshya Sivagami · **Points:** 1 · **Type:** test · **Area:** Testing & QA

*As the team, we want someone new to try the app without help, so that we know the UI meets NFR-01.*

Acceptance criteria:

- One person outside the team does upload → configure → evaluate → read result with no instructions.
- Observations are written up for the Test Report; each problem found becomes an issue (feeds US-18).

Requirements: NFR-01 · Test cases: TC-21 · Depends on: US-15
