# Sprint Plan
## Web-Based ML Model Evaluator

Two one-week sprints take the Deliverable 1 design to a working, tested application by **Tuesday 20 October 2026**. The user stories, acceptance criteria and requirement coverage are in the [Product Backlog](Product_Backlog.md).

---

## 1. Team and Roles

The work is split along the architecture's component boundaries ([Architecture §3](../deliverable-1/03_Architecture_and_Design.md#3-component-description)), so each person owns a separate part of the code and the parts meet only at the documented API contract (§10).

| Member | GitHub | Role | Owns (components) | Points (S1 + S2) |
|---|---|---|---|---|
| Adyanth | @Adyanth-212 | Team Lead / Scrum Master, Backend lead | Project setup, CI, component-separation check, API Controller, Evaluation Service, Result Service, API docs, integration, Test Report and demo | 15 + 15 = **30** |
| Akash MP | @Akash-MP19 | Validation & Security developer | Input Validation Service, Security/Policy Module, API Error Handler, Temporary Storage, Authentication Middleware | 11 + 11 = **22** |
| Akshath Patil | @akshathpatil353-oss | Frontend developer | Web UI (upload, configure, status, results, errors, download) | 9 + 8 = **17** |
| Akshya Sivagami | @Akshya-Sivagami | Metrics & QA developer | Metrics Service, reference test fixtures, determinism and usability tests | 8 + 2 = **10** |

Akshya's load is deliberately lighter because she produced Deliverable 1; the Team Lead carries the difference.

### 1.1 What each role does

**Adyanth — Team Lead / Scrum Master, Backend lead**
- Runs sprint planning, the mid-sprint check, sprint review and retrospective; keeps the GitHub milestones and issues up to date.
- Reviews and merges every pull request into `main`.
- Sets up the repository skeleton and CI on day 1 so everyone can start (EN-01) and adds an automated check that keeps the components separate (EN-04, NFR-09).
- Builds the Result Service and evaluation runner (EN-05, EN-06) and the evaluation API on top of them (US-01–US-05), documents the API (EN-07), wires the other components together, and owns the final Test Report and demo (EN-03, EN-08).

**Akash MP — Validation & Security**
- Makes sure nothing unsafe or invalid reaches model execution: file type/size, malformed inputs, configuration checks (US-06–US-08).
- Owns the safe error format, secure temporary storage and optional authentication (US-09–US-11).
- Writes the security test cases (TC-03–TC-07, TC-13, TC-14, TC-16–TC-18, TC-23).

**Akshath Patil — Frontend**
- Builds the whole browser workflow: Upload → Configure → Run → Results (US-12–US-18).
- Works against a mock of the API contract in Sprint 1 so the UI doesn't wait on the backend.
- Owns the look and usability of the app (NFR-01).

**Akshya Sivagami — Metrics & QA**
- Creates the reference models and datasets with known expected results that every test uses (EN-02) — this is on the critical path, so it is first.
- Implements the Metrics Service for classification and regression (US-19, US-20).
- Proves determinism (US-21) and runs the usability test with an outside user (US-22).

---

## 2. Sprints

### Sprint 1 — Wed 7 Oct to Tue 13 Oct 2026 (43 points)

**Goal:** a walking skeleton. A valid classification or regression evaluation works end to end — upload → validate → run → status → metrics on screen — and unsupported, oversized or malformed files are rejected.

| Adyanth | Akash MP | Akshath Patil | Akshya Sivagami |
|---|---|---|---|
| EN-01 Skeleton + CI (3) | US-06 File type/size (5) | US-12 Upload UI (3) | EN-02 Test fixtures (3) |
| EN-05 Result Service (2) | US-07 Malformed inputs (3) | US-13 Configure UI (3) | US-19 Classification metrics (3) |
| EN-06 Evaluation runner (3) | US-08 Config validation (3) | US-14 Run + status UI (3) | US-20 Regression metrics (2) |
| US-01 Submit evaluation (3) | | | |
| US-02 Status/results (3) | | | |
| EN-04 Component-separation check (1) | | | |

### Sprint 2 — Wed 14 Oct to Tue 20 Oct 2026 (36 points)

**Goal:** complete and hardened. Download, failure handling, safe errors, secure storage, optional authentication, every NFR checked, and all 25 test cases executed and reported.

| Adyanth | Akash MP | Akshath Patil | Akshya Sivagami |
|---|---|---|---|
| US-03 Download (3) | US-09 Safe errors (3) | US-15 Results view (3) | US-21 Determinism test (1) |
| US-04 Failures + limits (5) | US-10 Secure storage (5) | US-16 Error display (2) | US-22 Usability test (1) |
| US-05 2-second check (2) | US-11 Optional auth (3) | US-17 Download button (1) | |
| EN-07 API docs (2) | | US-18 Workflow polish (2) | |
| EN-03 Integration + Test Report (2) | | | |
| EN-08 Demo script + rehearsal (1) | | | |

---

## 3. Calendar

| Date | What happens |
|---|---|
| Wed 7 Oct | Sprint 1 planning (30 min): walk through this plan, confirm the decisions in §6, everyone picks up their first issue. |
| Thu 8 Oct | EN-01 skeleton + CI merged — everyone branches from it. EN-02 fixtures merged. |
| Sat 10 Oct | Mid-sprint check: each component works on its own with tests; UI runs against the mock API. |
| Mon 12 Oct | Integration day: UI talks to the real backend; happy path works end to end. |
| Tue 13 Oct | Sprint 1 review (demo the skeleton) + retrospective; move anything unfinished into Sprint 2. |
| Wed 14 Oct | Sprint 2 planning. |
| Sat 17 Oct | Mid-sprint check; usability test (US-22) once the results view is in. |
| Sun 18 Oct | **Feature freeze** — only bug fixes after this. |
| Mon 19 Oct | Full test run (all 25 test cases) and Test Report (EN-03). |
| Tue 20 Oct | Sprint 2 review, demo rehearsal, retrospective. **Done.** |

**Daily stand-up:** asynchronous, in the team group chat before 10 pm — three lines: *done yesterday / doing today / blocked by*. Blockers get sorted the same day.

---

## 4. How We Work

### 4.1 Issues and the board
- Every backlog item is a GitHub issue with its user story, acceptance criteria, linked requirements and test cases.
- Issues are grouped by milestone (**Sprint 1**, **Sprint 2**) and labelled by type (`user-story`, `enabler`, `test`) and area (`area: backend`, `area: validation`, `area: frontend`, `area: metrics`, `area: qa`, `area: infra`).
- New bugs or ideas go in as new issues; the Team Lead decides whether they enter the current sprint.

### 4.2 Branches, commits and pull requests
- Never commit directly to `main`. Branch per issue: `feat/US-06-file-validation`, `fix/US-09-trace-leak`.
- Commit messages: a short imperative summary line, then a body that says *what* changed and *why*.
- Open a pull request that says `Closes #<issue>` and lists which acceptance criteria and test cases it covers.
- CI must pass and the Team Lead (or another member for the Team Lead's own PRs) must approve before merge.
- Keep pull requests small — one issue each.

### 4.3 Definition of Done
An item is done only when:
1. every acceptance criterion is met;
2. the linked test cases are automated (or, for manual ones, written up) and pass in CI;
3. the pull request is reviewed and merged into `main`;
4. the SRS, Test Plan or Architecture document is updated if the implementation changed anything they state.

---

## 5. Dependencies to watch

```text
EN-01 skeleton ──┬─> US-06/07/08 validation ──> US-09 safe errors
                 ├─> EN-05 Result Service ──┬─> US-01 submit ──> US-05 timing, US-11 auth
                 │                          └─> US-02 status ──> US-03 download ──> EN-07 API docs
                 ├─> EN-06 evaluation runner (needs EN-05, EN-02) ──> US-04 failures + limits
                 └─> US-12 upload UI ──> US-13 ──> US-14 ──> US-15/16/17/18
EN-02 fixtures ──> US-19/20 metrics ──> US-21 determinism
```

EN-01, EN-02 and EN-05 unblock everyone, so they are due on **Thu 8 Oct**. Until the real pieces land, US-01 stubs validation and metrics, and the UI uses a mock API.

---

## 6. Decisions to confirm at Sprint 1 planning

| Decision | Proposal | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Async-friendly, generates OpenAPI docs for the §10 contract, same language as the ML libraries. |
| ML libraries | scikit-learn, pandas, joblib | Standard for classification/regression; metrics come built in. |
| Frontend | React + Vite (plain HTML/JS is an acceptable fallback) | Quick to build the four-step workflow; easy to mock the API. |
| Supported model format | scikit-learn models saved with joblib (`.joblib` / `.pkl`) | Simplest for users and fixtures. **Risk:** loading a pickle runs code inside it, so model loading must happen in an isolated, time-limited process (US-04, US-07) and this must be stated as a known limitation. |
| Result download format | JSON | Matches the API responses; CSV can be added if time allows. |
| Tests | pytest (+ FastAPI TestClient) in GitHub Actions | Every Test Plan case can be automated except the usability test. |

---

## 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Frontend blocked waiting for the backend | UI slips into Sprint 2 | Build against a mock of Architecture §10 from day 1. |
| Integration problems found late | Broken demo | Fixed integration day (Mon 12 Oct) and feature freeze (Sun 18 Oct). |
| Untrusted model files execute code on load | Security requirement not met | Isolated, time-limited process for loading and execution; documented limitation. |
| Someone is unavailable for a few days | Items stall | Stand-up blockers are raised the same day; the Team Lead reassigns. |
