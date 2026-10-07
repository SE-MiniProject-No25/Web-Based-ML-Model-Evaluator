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
├── planning/
│   ├── Product_Backlog.md
│   └── Sprint_Plan.md
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

## Deliverable 1

Deliverable 1 contains the following:

### 1. [Software Requirements Specification](deliverable-1/01_SRS.md)

The SRS documents the system purpose, scope, overall description, functional and non-functional requirements, security objectives and requirements, and UML use cases.

### 2. [Test Plan](deliverable-1/02_Test_Plan.md)

The Test Plan defines the testing strategy, test objectives, test environment, security validation, requirements traceability, and test cases covering functional and non-functional requirements.

### 3. [Software Architecture & Design Specification](deliverable-1/03_Architecture_and_Design.md)

This document describes the system architecture, architectural pattern, component structure, security architecture, UML sequence diagrams, API design, error handling, and design considerations.
