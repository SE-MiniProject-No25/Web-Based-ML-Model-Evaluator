# US-22 — Usability Test Report

## 1. Test Information

| Field | Details |
|---|---|
| User Story | US-22 — Run the usability test |
| Test Case | TC-21 |
| Requirement | NFR-01 |
| Test Type | Usability Testing |
| Participant | One person outside the project team |
| Test Date | On or before 3 Nov 2026. The exact day was not written down; this report was committed on 3 Nov 2026 (commit `8d265c7`) |
| Build Tested | `main` at `c280412` (3 Nov 2026, the frontend wizard from #47), the newest build on that day. It had no download control: the Download Results button came later, in #62 (10 Nov 2026) |
| Approximate Duration | 2 minutes |
| Assistance Provided | None |

## 2. Test Objective

To evaluate whether a person outside the development team can independently use the application to upload a machine-learning model and dataset, configure and execute an evaluation, and inspect the resulting metrics.

## 3. Test Procedure

The participant was given access to the application and the reference classification model and dataset.

The participant was asked to evaluate the supplied model and dataset and inspect the results. No step-by-step instructions or guidance were provided during the test.

## 4. Observations

| Application Area | Observation |
|---|---|
| Task Completion | Participant completed the primary workflow independently. |
| Time Taken | Approximately 2 minutes. |
| Upload | Participant was initially unsure which local files to select. |
| Configuration | Configuration options were easier to understand for users familiar with machine learning. |
| Evaluation | The evaluation button was easy to identify and use. |
| Results | Understanding the displayed metrics required some machine-learning knowledge. |
| Download | Participant did not notice the download control. *Correction (11 Nov 2026):* the build tested had no download control in the interface, so this observation records a missing feature, not a hidden one. It was added in #62. |
| Assistance | No assistance was requested. |
| Feedback | Limited feedback, primarily concerning the UI. |

## 5. Issues and Improvement Opportunities

1. Improve guidance for identifying the model and dataset files during upload.
2. Provide clearer descriptions for configuration options.
3. Add plain-language explanations for evaluation metrics.
4. Improve the visibility of the download control.

These are usability improvement recommendations identified during testing. Follow-up by the freeze (11 Nov 2026): recommendation 3 was implemented as plain-language metric explanations (#66), and recommendation 4 by the Download Results button (#62). Recommendations 1 and 2 are covered in part by the upload hints and the target-column list taken from the CSV header.

**Limitation:** one participant. A repeat with three participants was planned (TEST-02, #68) but did not take place before the freeze; see the Deviation Log, P-05.

## 6. Test Outcome

The participant successfully completed the primary evaluation workflow without assistance in approximately two minutes.

However, the observations indicate that certain parts of the interface assume familiarity with machine-learning concepts. In particular, configuration options and evaluation metrics may be difficult for users without an ML background. The download control also needs better visibility.

## 7. Conclusion

The usability test demonstrated that the primary evaluation workflow could be completed independently by a user outside the development team. The test also identified opportunities to improve the clarity and discoverability of interface elements.

The findings will be considered during the preparation of the System Validation Report.