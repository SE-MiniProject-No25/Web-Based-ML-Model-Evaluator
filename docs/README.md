# Documentation

Where every project document is. The reports in this folder are generated from the test run by `backend/scripts/generate_reports.py` (see each report's header for how to reproduce it).

## Test reports (Part 3)

| Report | What it contains |
|---|---|
| [Unit Test Report](Unit_Test_Report.md) | Unit tests by component, with results and what they cover |
| [System Validation Report](System_Validation_Report.md) | All 25 Test Plan cases with their results, security and performance validation, the browser tests, the usability test, and the defect list |
| [Code Coverage Report](Code_Coverage_Report.md) | Line coverage per file, with a reason for every line not covered |
| [Branch Coverage Report](Branch_Coverage_Report.md) | Branch coverage per file, with a reason for every branch not taken |
| [`coverage_html/`](coverage_html/index.html) | The browsable coverage report |

## Project records

| Document | What it contains |
|---|---|
| [Deviation Log](Deviation_Log.md) | Every difference between the plan and what was built, mapped to the documents, with a one-page summary for the demo |
| [Evaluator Checklist Audit](Evaluator_Checklist_Audit.md) | Each checklist line with its evidence and who explains it |
| [Viva Preparation](Viva_Prep.md) | Each member's work, the Agile process, and short answers on design and testing |
| [Release notes v1.0](Release_Notes_v1.0.md) | What the frozen version does, its quality figures and its known limitations |

## Elsewhere in the repository

| Document | Where |
|---|---|
| Software Requirements Specification | [`deliverable-1/01_SRS.md`](../deliverable-1/01_SRS.md) |
| Test Plan (test cases updated in Part 3) | [`deliverable-1/02_Test_Plan.md`](../deliverable-1/02_Test_Plan.md) |
| Architecture and Design Specification, UML | [`deliverable-1/03_Architecture_and_Design.md`](../deliverable-1/03_Architecture_and_Design.md), [`deliverable-1/uml/`](../deliverable-1/uml/) |
| Usability test report (US-22) | [`deliverable-1/usability-testing/`](../deliverable-1/usability-testing/) |
| Product Backlog, Sprint Plan (with Sprint 3 and the freeze), burndown | [`planning/`](../planning/) |
| Demo script (5 minutes) | [`planning/Demo_Script.md`](../planning/Demo_Script.md) |
| Sprint 1 video (1 minute), Sprint 2 video (2 minutes) and demo inputs | [`deliverable-1/Sprint1_Demo.mp4`](../deliverable-1/Sprint1_Demo.mp4), [`deliverable-2/`](../deliverable-2/) |
| API reference | `/docs` on a running backend, and the README "Run and try it" section |

The earlier Sprint 2 [Test Report](../planning/Test_Report.md) is superseded by the reports above.
