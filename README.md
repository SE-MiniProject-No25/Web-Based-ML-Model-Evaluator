# Web-Based ML Model Evaluator

A web-based software system for evaluating machine learning models against user-provided datasets and presenting standardized evaluation results through a web interface.

## Project Overview

The **Web-Based ML Model Evaluator** is a Software Engineering mini-project developed as a team project.

The system is intended to provide a structured interface through which users can upload a machine learning model and a dataset, validate the inputs, configure the evaluation, execute the model evaluation, and view or download the resulting metrics.

The project focuses on applying Software Engineering principles such as requirements engineering, UML-based modeling, software architecture, API design, security considerations, test planning, and traceability.

## Project Organization

This repository will contain the deliverables and implementation developed throughout the project.

```text
Web-Based-ML-Model-Evaluator/
│
├── README.md
│
├── backend/            # FastAPI service, one package per architecture component
├── frontend/           # React + Vite web UI
├── .github/            # CI workflow and pull request template
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

Additional deliverables and implementation files will be added to the repository as the project progresses.

The UML diagrams are written in [PlantUML](https://plantuml.com). After editing a `.puml` source, regenerate its image, for example with the PlantUML extension for VS Code or with:

```bash
java -jar plantuml.jar -tpng deliverable-1/uml/component.puml
```

## Project Planning

Implementation is planned as two one-week sprints (7 – 20 Oct 2026):

- [Product Backlog](planning/Product_Backlog.md) — user stories with acceptance criteria, mapped to every FR, NFR and test case.
- [Sprint Plan](planning/Sprint_Plan.md) — team roles, sprint goals, calendar, workflow and Definition of Done.
- [Sprint Burndown](planning/burndown/README.md) — burndown chart for the current sprint and how to refresh it.

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

Limits and switches (allowed extensions, upload size, evaluation time limit, retention period, authentication on/off) live in [`backend/app/config.py`](backend/app/config.py) and can be overridden with `MLEVAL_*` environment variables.

### Supported model format

scikit-learn models saved with `joblib` (`.joblib` or `.pkl`); datasets are `.csv`. **Known limitation:** loading a pickle runs code contained in the file, so models are only ever loaded by the evaluation component after validation, and execution is time-limited (see US-04 and US-07).

### Contributing

Branch per issue (`feat/US-06-file-validation`), never commit to `main`, and open a pull request that says `Closes #<issue>`. See [Sprint Plan §4](planning/Sprint_Plan.md).

## Deliverable 1

Deliverable 1 contains the following:

### 1. [Software Requirements Specification](deliverable-1/01_SRS.md)

The SRS documents the system purpose, scope, overall description, functional and non-functional requirements, security objectives and requirements, and UML use cases.

### 2. [Test Plan](deliverable-1/02_Test_Plan.md)

The Test Plan defines the testing strategy, test objectives, test environment, security validation, requirements traceability, and test cases covering functional and non-functional requirements.

### 3. [Software Architecture & Design Specification](deliverable-1/03_Architecture_and_Design.md)

This document describes the system architecture, architectural pattern, component structure, security architecture, UML sequence diagrams, API design, error handling, and design considerations.
