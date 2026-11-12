# Evaluator Checklist Audit
## Web-Based ML Model Evaluator

Every line of the evaluators' checklist, with where the evidence is and who explains it at the evaluation. **Status:** ✅ done, ⚠️ done with a caveat (explained), 🔲 still to do (owner named).

Checked on 11 Nov 2026, at the development freeze (tag `v1.0`).

## Part 1: Requirements and design documents

### Software Requirements Specification ([`deliverable-1/01_SRS.md`](../deliverable-1/01_SRS.md))

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| Standard IEEE format | ✅ | IEEE 830 structure: 1 Introduction (purpose, scope, definitions), 2 Overall description, 3 Specific requirements, 4 Security, 5 Use cases | Akshya |
| Introductory and descriptive sections | ✅ | §1.1–1.3, §2.1–2.6 | Akshya |
| FRs and NFRs, clear and measurable | ✅ | 20 FRs (§3.1); 10 NFRs (§3.2), each with a measurable acceptance criterion (for example NFR-02: 2 s over 10 runs) | Akshya |
| At least 1 UML use case diagram | ✅ | §5 "Use Case Diagram" ([`uml/use_case.png`](../deliverable-1/uml/use_case.png), PlantUML source alongside) | Akshya |
| Security: at least 2 objectives and 2 requirements | ✅ | §4.1 SO-01 to SO-03; §4.2 SEC-01 to SEC-08 | Akash |

### Test Plan ([`deliverable-1/02_Test_Plan.md`](../deliverable-1/02_Test_Plan.md))

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| Standard IEEE format | ✅ | IEEE 829 structure: introduction, strategy, test cases and procedures, environment and criteria, procedures, risks, traceability | Akshya |
| Sections 3, 4 and 5 completely filled | ✅ | §3 Test cases and procedures (3.1–3.2), §4 Environment, tools, entry/exit and pass/fail (4.1–4.4), §5 Procedures (5.1–5.4) | Akshya |
| Section 5.1 dedicated to security validation | ✅ | §5.1 Security Validation | Akash |
| Clear traceability back to the SRS | ✅ | §7 Requirements Traceability Matrix (every FR, NFR and SEC to test cases); §9 maps each case to its automated tests, checked by `backend/tests/test_traceability.py` | Adyanth |
| At least 7–10 test cases covering FRs and NFRs | ✅ | 25 test cases, TC-01 to TC-25 (§8) | Akshya |

### Architecture and Design ([`deliverable-1/03_Architecture_and_Design.md`](../deliverable-1/03_Architecture_and_Design.md))

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| Standard IEEE format | ✅ | IEEE 1016 style: Part I architecture, Part II detailed design | Adyanth |
| Component diagrams and descriptions, pattern, traceability, security architecture | ✅ | §2.1 layered pattern, §3 components, §4 component diagram, §6 security architecture, §7 traceability | Adyanth, Akash (§6) |
| At least 2 UML sequence diagrams, API design, error handling | ✅ | §8 evaluation and §9 upload-validation sequence diagrams, §10 API design, §11 error handling | Adyanth |

## Part 2: Agile planning and repository

### Backlog and project management

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| GitHub Project created and linked to the repository | ✅ | The project board exists and is linked to the repository; sprints are also GitHub milestones (Sprint 1, 2, 3) | Adyanth |
| Backlog items created from the SRS FRs and NFRs | ✅ | [Product Backlog](../planning/Product_Backlog.md) §2 maps every FR, NFR and test case to a backlog item; issues #1–#30 | Adyanth |
| Story points on all backlog items | ✅ | Product Backlog §1: every item has points (79 in total) | Adyanth |
| User stories assigned to individual members | ✅ | Product Backlog "Owner" column; every issue has an assignee | Adyanth |
| Sprint 1 and Sprint 2 planned on the board | ✅ | Milestones *Sprint 1* (15 issues) and *Sprint 2* (15 issues); [Sprint Plan](../planning/Sprint_Plan.md) §2. *Sprint 3* (15 issues) added for the spill-over and Part-3 testing (§2a) | Adyanth |

### Sprint 1

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| GitHub Actions enabled for pull requests and commits | ✅ | [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): backend lint and tests on Linux and Windows with coverage thresholds, frontend lint, tests and build, browser tests. Runs on every pull request and every push to `main` | Adyanth |
| Code implemented with approved methods, matching SRS/SAD | ✅ | Matches the SAD components and API (README "Code Map"; `test_architecture.py` enforces the boundaries). Differences are in the [Deviation Log](Deviation_Log.md) | Everyone |
| Pull requests raised by the assigned member | ✅ | Akash: #38–#40, #56–#58; Akshya: #41–#43, #46, #51, #55; Akshath: #59, #61, #62, #65; Adyanth: the rest. See [Viva Prep](Viva_Prep.md) §1 | Everyone |
| Pull requests formally reviewed and merged by the repository owner | ⚠️ | All were merged by the team lead; formal GitHub reviews only on #34, #35, #42, #44. Recorded as deviation [P-04](Deviation_Log.md#2-process-deviations). Branch protection with a required review is on after the freeze | Adyanth |
| 1-minute Sprint 1 video in the repository | ✅ | [`deliverable-1/Sprint1_Demo.mp4`](../deliverable-1/Sprint1_Demo.mp4) (1:18) | Akshya |

### Sprint 2

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| Sprint 2 completed and development officially frozen | ✅ | All Sprint 2 stories closed (in Sprint 3, see Sprint Plan §2a); freeze recorded in Sprint Plan §2b and the README, tag `v1.0` | Adyanth |
| Deviations from SAD/SRS documented for the demo | ✅ | [Deviation Log](Deviation_Log.md) (design D-01–D-16, process P-01–P-06) with a one-page summary (§3); each affected document links to it | Adyanth |
| All remaining documentation finalised | ✅ | [docs index](README.md); documents updated to the final code (DOC-05) | Adyanth |
| 2-minute video in the repository | ✅ | [`deliverable-2/Sprint2_Demo.mp4`](../deliverable-2/Sprint2_Demo.mp4) (2:00, screen recording) | Adyanth |

## Part 3: Testing and quality assurance

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| Original test cases updated for the sprint changes | ✅ | Test Plan §8 updated (Part 3): TC-15, TC-18, TC-19 and the authentication, retention and download cases describe what was built | Adyanth |
| All tests executed according to the Test Plan | ✅ | [System Validation Report](System_Validation_Report.md): all 25 cases, 24 automated plus TC-21 by hand | Adyanth |
| Generated reports in `docs/` | ✅ | [Unit Test](Unit_Test_Report.md), [System Validation](System_Validation_Report.md), [Code Coverage](Code_Coverage_Report.md), [Branch Coverage](Branch_Coverage_Report.md) reports, regenerated on the final code by `backend/scripts/generate_reports.py` | Adyanth |

## Part 4: Final evaluation

| Checklist line | Status | Evidence | Explains |
|---|---|---|---|
| The application works as designed and fulfils the core use cases | ✅ | UC-01 to UC-03 run end to end in the browser tests (`e2e/`) and the [demo script](../planning/Demo_Script.md); `python scripts/demo_check.py` checks the 9 demo scenarios | Everyone |
| The team explains permitted deviations | ✅ | Deviation Log §3, one page | Adyanth |
| Codebase accessible, readable, under version control | ✅ | Public GitHub repository, README with setup, code map and API examples; every change through a pull request | Everyone |
| Each member explains their code and demonstrates their pull requests | ✅ | [Viva Prep](Viva_Prep.md) §1 lists each member's issues, pull requests and files | Everyone |
| The team understands the Agile process (estimates, sprints, blockages) | ✅ | Viva Prep §2 (points planned and delivered, Sprint 3, blockages and how they were resolved) | Adyanth |
| The team justifies architecture, API design and testing results | ✅ | Viva Prep §3 | Everyone |
