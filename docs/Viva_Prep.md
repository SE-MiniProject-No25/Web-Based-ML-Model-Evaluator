# Viva Preparation
## Web-Based ML Model Evaluator

For the oral examination (checklist Part 4): each member's own work, the Agile process, and short answers to the likely questions on design and testing. Everything here is taken from the repository history; follow the links to show the evidence.

## 1. Who did what

Open your pull requests on GitHub before the viva and be ready to walk through one of them: what it changes, how it is tested, and one decision you made.

| Member | Role | Backlog items | Pull requests | Main files |
|---|---|---|---|---|
| **Adyanth** (@Adyanth-212) | Team lead, backend | EN-01, EN-03–EN-08, US-01–US-05; Sprint 3: TEST-01, 03, 04, 05, 06, 07, 10, 11, DOC-01–06 | #31–#36, #44, #45, #47–#50, #52–#54, #60, #63, #66, #85–#93 | `backend/app/api/evaluations.py`, `app/evaluation/` (runner, worker), `app/results/`, `app/validation/service.py` (spare inspectors), `app/api/retention.py`, `app/security/memory_limit.py`, `tests/test_architecture.py`, `.github/workflows/ci.yml`, `scripts/generate_reports.py`, `frontend/src/test/`, `e2e/` |
| **Akash MP** (@Akash-MP19) | Validation and security | US-06, US-07, US-08, US-09, US-10, US-11 (issues US-23–US-28, #25–#30) | #38, #39, #40, #56, #57, #58 | `backend/app/validation/service.py` (file type, size, CSV and model checks), `app/validation/model_inspector.py`, `app/api/error_handlers.py`, `app/storage/` (temporary storage, retention), `app/api/auth.py`, `tests/test_api_submit.py`, `test_storage.py`, `test_auth.py`, `test_errors.py` |
| **Akshath Patil** (@akshathpatil353-oss) | Frontend | US-12–US-18 | #59, #61, #62, #65 (and the UI that #45 and #47 connected) | `frontend/src/App.jsx`, `App.css`, `api.js` (error handling, download), `mockAPI.js` |
| **Akshya Sivagami** (@Akshya-Sivagami) | Metrics and QA | EN-02, US-19, US-20, US-21, US-22; Deliverable 1 documents | #41, #42, #43, #46, #51, #55 | `backend/app/metrics/service.py`, `tests/test_metrics_service.py`, `tests/fixtures/` and `generate_fixtures.py`, `tests/test_determinism.py`, `deliverable-1/` (SRS, Test Plan, SAD, UML), usability report, Sprint 1 video |

## 2. The Agile process

**Estimation.** Story points on a 1-2-3-5-8 scale for relative effort, not hours: 79 points for 30 backlog items ([Product Backlog](../planning/Product_Backlog.md) §1). Work was split along the architecture's components, so each person owned separate code that met the others only at the API contract.

**Sprints planned against delivered** ([Sprint Plan](../planning/Sprint_Plan.md) §2a):

| Sprint | Dates | Planned | Delivered |
|---|---|---|---|
| 1 | 7–13 Oct | 43 points | 26 merged 14 Oct (one day late); the other 17 by 28 Oct |
| 2 | 14–20 Oct | 36 points | none by 20 Oct; all 36 on 3–10 Nov |
| 3 (spill-over) | 3–11 Nov | Sprint 2's 36 + Part-3 testing | all, plus 11 testing and debugging items; frozen at `v1.0` |

**Blockages and how they were resolved:**
- **A Windows-only bug** (#44): every valid model was rejected on Windows, because the validation child process could not import joblib with the stripped environment. CI ran on Linux only, so it passed there. Fixed by giving the child the server's `sys.path`. Prevented since by running CI on Windows too (#88).
- **Two frontends built in parallel** (#45, #46): the frontend developer built against the mock API while the team lead wired the real API. They were combined in #47.
- **Stacked pull requests and merge conflicts:** dependent pull requests (for example #57/#58 on storage and auth) conflicted. They were resolved on their branches and merged bottom-up; branches are deleted on merge so the stack retargets itself.
- **Large file in git:** the Sprint 1 video is 67 MB. The Sprint 2 video was recorded at 7 MB, and models and media are marked binary (#87).
- **Overrun:** 26 of 79 points by the planned end, so a Sprint 3 was declared, as the Part-3 brief allows (Deviation Log P-01, P-02).

**Process rules:** a branch per issue, a pull request that closes the issue, CI on every pull request, and a Definition of Done (Sprint Plan §4). Where reality differed (reviews), it is in the Deviation Log (P-04).

## 3. Likely questions, short answers

**Why a layered architecture with these components?** Each SAD component is one package (`backend/app/api`, `validation`, `evaluation`, `metrics`, `results`, `storage`, `security`). A lower layer never imports a higher one, and `tests/test_architecture.py` fails the build if it does (NFR-09). That lets four people work in parallel and keeps the security-relevant code (validation, storage, execution) separate and testable.

**Why run the model in a separate process?** Loading a pickle or joblib file runs code inside it. The server never loads one. A child process with a sanitized environment (no server secrets), a time limit and a memory limit (Linux and macOS via `setrlimit`, Windows via a job object) checks the model before the `202` and runs it afterwards. It is process isolation, not a container, and that is stated as a limitation (DEF-06).

**Why `202 Accepted` and polling?** An evaluation can take seconds. The `POST` returns at once with an ID (NFR-02: within 2 s), the work runs in the background, and the client polls `GET /api/evaluations/{id}` until the status is `completed` or `failed`. The status moves only forward (`pending → running → completed | failed`).

**Why these three endpoints?** They map one-to-one to the use cases: submit (UC-01), status and result (UC-01/02), download (UC-03). IDs are random UUIDs, so results cannot be found by guessing (SAD §6.2).

**Why one error format?** Every error, including 404/405/500, is `{"error": {"code", "message"}}` with a code from SAD §11. Messages are safe: no stack traces or paths (SEC-05). Errors after the `202` are not HTTP errors: the status becomes `failed` and carries the same error object.

**How fast is the acknowledgement, and why?** Almost all the time before the `202` was the check process importing scikit-learn (1.56 s). Two spare inspector processes now wait with scikit-learn already loaded, and each model is still checked in its own fresh process. About 0.2 s at normal pace (#91).

**What do the automated tests show?** See the reports in `docs/`:
- **Backend:** hundreds of pytest tests, unit and system, with line and branch coverage above the 90% and 85% CI thresholds. Every remaining uncovered line has a stated reason.
- **Frontend:** Vitest component and API tests.
- **Browser:** Playwright tests of the whole workflow.
- **Test Plan:** all 25 cases pass, 24 automated plus the usability test by hand. Exact figures are in the [System Validation Report](System_Validation_Report.md).

**What is not done or is limited?**
- Process isolation, not a container.
- Results are in memory for the session.
- Download is JSON only.
- The usability test had one participant; the planned repeat did not happen before the freeze (Deviation Log P-05).

**What changed from the design?** See the one-page summary in the [Deviation Log](Deviation_Log.md#3-one-page-summary-for-the-demo).

## 4. Before the viva

- [ ] `python backend/scripts/demo_check.py` passes against a running backend
- [ ] Each presenter has read their part of the [5-minute demo script](../planning/Demo_Script.md) (no team rehearsal was held, Deviation Log P-05)
- [ ] Each member has opened their pull requests and can explain one in detail
- [ ] Each member has read the [Deviation Log](Deviation_Log.md) summary
