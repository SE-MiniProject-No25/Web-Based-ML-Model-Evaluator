# Release notes: v1.0
## Web-Based ML Model Evaluator

The version frozen at the end of Sprint 3 (11 Nov 2026) for the final evaluation. After it, only bug fixes are merged, each through a reviewed pull request.

## What it does

Upload a scikit-learn model (`.joblib` / `.pkl`) and a CSV dataset, choose classification or regression and the target column, and get standard metrics in a table with plain-language explanations and a chart. The result downloads as JSON.
- **Classification:** accuracy, precision, recall and F1.
- **Regression:** MAE, MSE, RMSE and R².

The same workflow is available as a documented REST API (`/docs`).

## Highlights
- **Safe handling of untrusted models.** A model is never loaded in the server. It is checked and run in separate child processes with a sanitized environment, a time limit and a memory limit (Linux, macOS and Windows).
- **Validation before anything runs:**
  - File type and size are checked first.
  - Malformed CSVs and corrupt models are rejected.
  - The task type and target column are checked on the server.
  - Clear messages explain data that doesn't suit the model or the task.
- **One error format** everywhere (`{"error": {"code", "message"}}`), with no internal details exposed.
- **Optional API-key authentication**, unguessable evaluation IDs, uploads stored under random names, and expired uploads removed on a timer.
- **About 0.2 s to acknowledge a submission** at normal pace (requirement: 2 s).

## Quality
- **Backend:** pytest unit and system tests, run on Linux and Windows in CI. CI fails under 90% line or 85% branch coverage.
- **Frontend:** Vitest component and API tests.
- **Browser:** Playwright tests of the whole workflow.
- **Test Plan:** all 25 test cases pass, as reported in the [System Validation Report](System_Validation_Report.md). The other reports are in [`docs/`](README.md).

## Known limitations
- Process isolation, not a container: a malicious model can still run code with the server user's rights.
- Results are kept in memory for the session.
- Download is JSON only.
- See the [Deviation Log](Deviation_Log.md) for every difference from the original design.
