# Demo inputs

Models and datasets for demonstrating, testing and recording the Web-Based ML Model Evaluator. Everything is small (217 KB in total) and **deterministic**: `python make_demo_inputs.py` recreates every file, and `python make_demo_inputs.py --verify` submits each one to the real application code and prints what happened. The figures below come from that run.

In the interface: choose the model and the dataset on the Upload step, then pick the **task** and **target column** shown in the tables.

## Inputs that should work

| Model | Dataset | Task | Target column | What it shows | Result |
|---|---|---|---|---|---|
| `01_churn_model.joblib` | `01_churn_data.csv` | classification | `churned` | Binary classification, logistic regression | accuracy 0.7444, precision 0.7416, recall 0.7416, F1 0.7416 |
| `02_iris_model.pkl` | `02_iris_data.csv` | classification | `species` | **Three classes** (scores averaged across them); a `.pkl` model | accuracy 0.9778, precision 0.9792, recall 0.9778, F1 0.9778 |
| `03_house_price_model.joblib` | `03_house_price_data.csv` | regression | `price` | Regression with a random forest | MAE 29.1741, MSE 1267.7001, RMSE 35.6048, R² 0.8965 |
| `04_loan_model.joblib` | `04_loan_data.csv` | classification | `approved` | Decision tree; precision higher than recall | accuracy 0.7200, precision 0.8116, recall 0.6588, F1 0.7273 |
| `05_energy_model.joblib` | `05_energy_data.csv` | regression | `energy_kwh` | A plain linear model with a very high R² | MAE 1.2783, MSE 2.4625, RMSE 1.5692, R² 0.9572 |
| `06_cancer_pipeline_model.joblib` | `06_cancer_data.csv` | classification | `diagnosis` | A **scikit-learn Pipeline** (scaler + model) on a real dataset with 30 features | accuracy 0.9750, precision 0.9762, recall 0.9840, F1 0.9801 |

## Inputs that should be refused, or fail clearly

| Model | Dataset | Task / target | What the application does |
|---|---|---|---|
| `01_churn_model.joblib` | `bad_ragged_rows.csv` | classification / `churned` | Rejected, `422 MALFORMED_DATASET`: "The dataset file contains ragged rows with inconsistent column counts." The message appears next to the dataset field |
| `01_churn_model.joblib` | `bad_empty.csv` | classification / `churned` | Rejected, `422 MALFORMED_DATASET`: "The dataset file is empty." (the interface also refuses an empty CSV before sending it) |
| `01_churn_model.joblib` | `bad_wrong_columns.csv` | classification / `label` | Accepted, then **fails** with `INCOMPATIBLE_INPUTS`, naming the columns the model expects and the ones it did not use |
| `01_churn_model.joblib` | `01_churn_data.csv` | classification / **`tenure_months`** | The classic mistake: a *feature* picked as the target. Fails with `INCOMPATIBLE_INPUTS`: "Missing from the dataset: tenure_months. Not used by the model: churned." |
| `bad_unsupported_model.txt` | `01_churn_data.csv` | classification / `churned` | The interface says "Please select a .pkl or .joblib model file." If sent to the API anyway: `415 UNSUPPORTED_FILE_TYPE` |
| `bad_corrupt_model.joblib` | `01_churn_data.csv` | classification / `churned` | Rejected, `422 INVALID_MODEL`: "The model file could not be loaded or is corrupted." The model is opened in a separate process, never in the server |
| `bad_not_a_model.joblib` | `01_churn_data.csv` | classification / `churned` | A valid file that is not a model. Rejected, `422 INVALID_MODEL`: "The model file must have a callable predict method." |
| `01_churn_model.joblib` | `01_churn_data.csv` | **`clustering`** / `churned` | `422 INVALID_TASK_TYPE` (only possible through the API; the interface offers two choices) |
| `01_churn_model.joblib` | `01_churn_data.csv` | classification / **`no_such_column`** | `422 INVALID_TARGET_COLUMN` (only possible through the API; the interface lists the real columns) |

## More things to try from a terminal

Run from the repository root (in Windows PowerShell write `curl.exe`).

```bash
# A path-like filename is stored under a random name and cannot reach outside the storage folder
curl -s -X POST http://127.0.0.1:8000/api/evaluations \
  -F model=@deliverable-2/demo-inputs/01_churn_model.joblib \
  -F "dataset=@deliverable-2/demo-inputs/01_churn_data.csv;filename=../../evil.csv" \
  -F task_type=classification -F target_column=churned

# A file over the 10 MB limit is refused with 413 FILE_TOO_LARGE (create one first)
python -c "open('big.csv','wb').write(b'a,b\n' + b'1,2\n' * 3_000_000)"
curl -s -X POST http://127.0.0.1:8000/api/evaluations \
  -F model=@deliverable-2/demo-inputs/01_churn_model.joblib -F dataset=@big.csv \
  -F task_type=classification -F target_column=b
```

To see **authentication**, start the backend with `MLEVAL_AUTH_ENABLED=true` and `MLEVAL_API_KEY=demo-key`. A request without the key is then answered with `401 UNAUTHENTICATED`; add `-H "X-API-Key: demo-key"` and it succeeds (covered by `backend/tests/test_auth.py`).

## Unusual inputs

The debugging pass (issue #83) tried text class labels such as `yes` / `no`, CSV headers with spaces after the commas, an Excel byte-order mark, semicolon- and tab-separated files, empty cells, text in numeric columns, and the wrong task type for the data. Each now either works or is stopped with a message that says what to change. They are kept as automated tests in `backend/tests/test_edge_case_inputs.py`, so they are not repeated in this pack.
