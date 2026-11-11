# Web-Based ML Model Evaluator

A web-based software system for evaluating machine learning models against user-provided datasets and presenting standardized evaluation results through a web interface.

## Project Overview

The **Web-Based ML Model Evaluator** is a Software Engineering mini-project developed as a team project.

The system is intended to provide a structured interface through which users can upload a machine learning model and a dataset, validate the inputs, configure the evaluation, execute the model evaluation, and view or download the resulting metrics.

The project focuses on applying Software Engineering principles such as requirements engineering, UML-based modeling, software architecture, API design, security considerations, test planning, and traceability.

## Project Organization

This repository contains the deliverables and the implementation developed throughout the project.

```text
Web-Based-ML-Model-Evaluator/
│
├── README.md
│
├── backend/            # FastAPI service, one package per architecture component
├── frontend/           # React + Vite web UI
├── .github/            # CI workflow and pull request template
│
├── docs/               # test reports, deviation log, checklist audit, viva prep (see docs/README.md)
├── e2e/                # browser tests of the whole workflow
│
├── planning/
│   ├── Product_Backlog.md
│   ├── Sprint_Plan.md
│   └── burndown/
│
└── deliverable-1/
    ├── 01_SRS.md
    ├── 02_Test_Plan.md
    ├── 03_Architecture_and_Design.md
    │
    └── uml/
        ├── use_case.puml / use_case.png
        ├── component.puml / component.png
        ├── sequence_evaluation.puml / sequence_evaluation.png
        └── sequence_validation.puml / sequence_validation.png
```

`deliverable-2/` holds the 2-minute Sprint 2 video, its recording script and the demo inputs.

The UML diagrams are written in [PlantUML](https://plantuml.com). After editing a `.puml` source, regenerate its image, for example with the PlantUML extension for VS Code or with:

```bash
java -jar plantuml.jar -tpng deliverable-1/uml/component.puml
```

## Project Planning

> **Development is frozen** as of 11 Nov 2026 at tag [`v1.0`](https://github.com/SE-MiniProject-No25/Web-Based-ML-Model-Evaluator/releases/tag/v1.0). After the freeze only bug fixes are merged, each through a reviewed pull request. All documents are indexed in [`docs/README.md`](docs/README.md); differences from the original design are in the [Deviation Log](docs/Deviation_Log.md).

Implementation was planned as two one-week sprints (7 – 20 Oct 2026); they overran, and a third sprint (3 – 11 Nov) finished the spill-over and the Part-3 testing ([Sprint Plan §2a](planning/Sprint_Plan.md#2a-what-actually-happened-and-sprint-3)):

- [Product Backlog](planning/Product_Backlog.md) — user stories with acceptance criteria, mapped to every FR, NFR and test case.
- [Sprint Plan](planning/Sprint_Plan.md) — team roles, sprint goals, calendar, workflow and Definition of Done.
- [Demo Script](planning/Demo_Script.md) — the 5-minute demo, who presents what, and backup screenshots.
- [Test reports](docs/) — [Unit Test Report](docs/Unit_Test_Report.md), [System Validation Report](docs/System_Validation_Report.md), [Code Coverage Report](docs/Code_Coverage_Report.md) and [Branch Coverage Report](docs/Branch_Coverage_Report.md) (Part 3). The earlier Sprint 2 [Test Report](planning/Test_Report.md) is superseded.
- [Sprint Burndown](planning/burndown/README.md) — burndown chart for the current sprint and how to refresh it.

## Demo

- **[Sprint 2 demo video](deliverable-2/Sprint2_Demo.mp4)** (2 minutes): a screen recording of the working product end to end, with [what each part shows](deliverable-2/README.md#what-the-video-shows). The earlier [Sprint 1 video](deliverable-1/Sprint1_Demo.mp4) shows the first working version.
- **[Demo inputs](deliverable-2/demo-inputs/)**: six good models and datasets and nine bad inputs to try in the interface, with what each one shows. The [demo script](planning/Demo_Script.md) is the 5-minute live version.

## Code Map

Each code folder maps to one component in [Architecture §3](deliverable-1/03_Architecture_and_Design.md#3-component-description). The boundaries are enforced by [`backend/tests/test_architecture.py`](backend/tests/test_architecture.py), which runs in CI and fails if a lower layer imports an upper one.

| Code | Architecture component | May import from |
|---|---|---|
| [`frontend/src`](frontend/src) | Web UI (talks to the backend only through the API contract, §10) | — |
| [`backend/app/api`](backend/app/api) | API Controller, API Error Handler, Authentication Middleware | validation, evaluation, metrics, results, storage, security |
| [`backend/app/validation`](backend/app/validation) | Input Validation Service | security |
| [`backend/app/evaluation`](backend/app/evaluation) | Evaluation Service | metrics, results, storage, security |
| [`backend/app/metrics`](backend/app/metrics) | Metrics Service | — |
| [`backend/app/results`](backend/app/results) | Result Service | — |
| [`backend/app/storage`](backend/app/storage) | Temporary Storage (+ Storage Lifecycle Manager) | security |
| [`backend/app/security`](backend/app/security) | Security/Policy Module | — |
| [`backend/app/errors.py`](backend/app/errors.py), [`config.py`](backend/app/config.py) | Shared error type and settings (import no component) | — |
| [`backend/app/main.py`](backend/app/main.py) | Composition root that wires the components together | any |

Every row may also import `errors` and `config`. Backend code never imports frontend code.

## Getting Started

**Tech stack:** Python 3.11+ with FastAPI, scikit-learn, pandas and joblib on the backend; React + Vite on the frontend; pytest and ruff in CI.

**Backend** (from the repository root):

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload      # http://127.0.0.1:8000, docs at /docs
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Tests and lint:**

```bash
cd backend
ruff check .
pytest
```

**Browser tests** (the whole workflow in a real browser; they start their own backend and frontend):

```bash
pip install -r e2e/requirements.txt
python -m playwright install chromium
python -m pytest e2e          # E2E_BROWSER_CHANNEL=msedge uses the installed Edge instead
```

Limits and switches (allowed extensions, upload size, evaluation time and memory limits, retention period, authentication on/off) live in [`backend/app/config.py`](backend/app/config.py) and can be overridden with `MLEVAL_*` environment variables.

### Supported model format

scikit-learn models saved with `joblib` (`.joblib` or `.pkl`); datasets are `.csv`. **Known limitation:** loading a pickle runs code contained in the file, so models are only ever loaded in a separate child process with a sanitized environment, after validation. The evaluation run is stopped at the configured time limit and at the configured memory limit (on Linux and macOS the worker limits its own address space; on Windows the server puts it in a job object with a memory limit). This is process isolation, not a container sandbox.

### Contributing

Branch per issue (`feat/US-06-file-validation`), never commit to `main`, and open a pull request that says `Closes #<issue>`. See [Sprint Plan §4](planning/Sprint_Plan.md).

## Run and try it

Start the backend (see [Getting Started](#getting-started)), then open **http://127.0.0.1:8000/docs** for the interactive API documentation: every endpoint, request field, response and error code from [Architecture §10–11](deliverable-1/03_Architecture_and_Design.md#10-api-design), with a *Try it out* button. The same information as plain commands, run from the repository root (in Windows PowerShell write `curl.exe` instead of `curl`):

**1. Submit an evaluation.** Answered at once with `202`; the evaluation runs in the background.

```bash
curl -s -X POST http://127.0.0.1:8000/api/evaluations   -F model=@backend/tests/fixtures/classification/model.joblib   -F dataset=@backend/tests/fixtures/classification/data.csv   -F task_type=classification   -F target_column=label
```
```json
{"evaluation_id":"3b7e2a3d-d3c3-4c29-9eed-a1ddc3c1a5d3","status":"pending"}
```

**2. Check the status.** Repeat until `status` is `completed` or `failed` (a few seconds).

```bash
curl -s http://127.0.0.1:8000/api/evaluations/3b7e2a3d-d3c3-4c29-9eed-a1ddc3c1a5d3
```
```json
{"evaluation_id":"3b7e2a3d-…","status":"completed","task_type":"classification","metrics":{"accuracy":0.9625,"precision":0.9767441860465116,"recall":0.9545454545454546,"f1":0.9655172413793104}}
```

**3. Download the result** as a file (`-OJ` saves it under the name the server gives it, `evaluation-<id>.json`).

```bash
curl -s -OJ http://127.0.0.1:8000/api/evaluations/3b7e2a3d-d3c3-4c29-9eed-a1ddc3c1a5d3/download
```

Mistakes come back in one format, `{"error": {"code", "message"}}`, with the status from the architecture's error table: an unknown ID is `404 EVALUATION_NOT_FOUND`, downloading before the evaluation has completed is `409 EVALUATION_NOT_COMPLETED`, and for example `task_type=clustering` is `422 INVALID_TASK_TYPE`. An evaluation that goes wrong *after* the `202` (wrong columns, a time or memory limit, a crash) is not an HTTP error: its status becomes `failed` and the status endpoint returns the same `error` object.

Reference models and datasets to try are in `backend/tests/fixtures/`: `classification/` (target column `label`, task `classification`) and `regression/` (target column `price`, task `regression`).

### Using the API from the frontend

The frontend needs nothing beyond this section. In development Vite forwards every `/api/...` request to the backend on port 8000 (`frontend/vite.config.js`), and `frontend/src/api.js` calls the three endpoints above. Set `VITE_USE_MOCK=true` to use the in-memory mock instead (for example when the backend is not running); leave it unset to use the real API. Poll the status endpoint about once a second until the status is `completed` or `failed`.

### Authentication

Optional and off by default. Start the backend with `MLEVAL_AUTH_ENABLED=true` and `MLEVAL_API_KEY=<a secret>`; every request to the evaluation endpoints must then carry the key, either as `X-API-Key: <key>` or as `Authorization: Bearer <key>`, and is otherwise answered with `401 UNAUTHENTICATED`. `/api/health` stays open. If authentication is enabled with no key configured, every protected request is rejected. Every error, including unknown URLs (`404`), unsupported methods (`405`) and unexpected server errors (`500`), uses the `{"error": {"code", "message"}}` format.

## Deliverable 1

Deliverable 1 contains the following:

### 1. [Software Requirements Specification](deliverable-1/01_SRS.md)

The SRS documents the system purpose, scope, overall description, functional and non-functional requirements, security objectives and requirements, and UML use cases.

### 2. [Test Plan](deliverable-1/02_Test_Plan.md)

The Test Plan defines the testing strategy, test objectives, test environment, security validation, requirements traceability, and test cases covering functional and non-functional requirements.

### 3. [Software Architecture & Design Specification](deliverable-1/03_Architecture_and_Design.md)

This document describes the system architecture, architectural pattern, component structure, security architecture, UML sequence diagrams, API design, error handling, and design considerations.
