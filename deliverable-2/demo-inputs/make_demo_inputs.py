"""Create the demo models and datasets used in the Sprint 2 video, and check what the application does with each.

    python make_demo_inputs.py            # (re)create every file next to this script
    python make_demo_inputs.py --verify   # also submit each one to the real application code and print the outcome

Everything is deterministic (fixed random seeds), so the files and the figures in README.md can be reproduced.
Needs the backend dependencies (see backend/requirements-dev.txt).
"""

import argparse
import sys
import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer, load_iris
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / "backend"


def save(model, name: str) -> None:
    joblib.dump(model, HERE / name, compress=3)


# --- good inputs -------------------------------------------------------------------------------------------


def churn() -> None:
    """Binary classification: will a customer leave? (logistic regression)"""
    rng = np.random.default_rng(42)
    n = 600
    df = pd.DataFrame(
        {
            "tenure_months": rng.integers(1, 72, n),
            "monthly_charge": rng.normal(65, 20, n).round(2),
            "support_calls": rng.poisson(2, n),
            "contract_years": rng.choice([1, 2, 3], n, p=[0.6, 0.25, 0.15]),
        }
    )
    score = -0.04 * df.tenure_months + 0.03 * df.monthly_charge + 0.45 * df.support_calls - 0.5 * df.contract_years
    df["churned"] = ((score + rng.normal(0, 1.2, n)) > score.median()).astype(int)
    train, test = train_test_split(df, test_size=0.3, random_state=0)
    features = [c for c in df if c != "churned"]
    save(LogisticRegression(max_iter=1000).fit(train[features], train.churned), "01_churn_model.joblib")
    test.to_csv(HERE / "01_churn_data.csv", index=False)


def iris() -> None:
    """Multiclass classification (3 species), saved as .pkl to show both formats."""
    frame = load_iris(as_frame=True).frame.rename(columns={"target": "species"})
    frame.columns = [c.replace(" (cm)", "").replace(" ", "_") for c in frame.columns]
    train, test = train_test_split(frame, test_size=0.3, random_state=1, stratify=frame.species)
    features = [c for c in frame if c != "species"]
    save(RandomForestClassifier(n_estimators=30, max_depth=5, random_state=0).fit(train[features], train.species),
         "02_iris_model.pkl")  # fmt: skip
    test.to_csv(HERE / "02_iris_data.csv", index=False)


def houses() -> None:
    """Regression: house price in thousands."""
    rng = np.random.default_rng(7)
    n = 500
    df = pd.DataFrame(
        {
            "area_sqft": rng.integers(600, 3500, n),
            "bedrooms": rng.integers(1, 6, n),
            "age_years": rng.integers(0, 60, n),
            "distance_to_city_km": rng.uniform(1, 40, n).round(1),
        }
    )
    df["price"] = (
        0.12 * df.area_sqft + 18 * df.bedrooms - 1.1 * df.age_years - 2.5 * df.distance_to_city_km + 80
        + rng.normal(0, 25, n)  # fmt: skip
    ).round(1)
    train, test = train_test_split(df, test_size=0.3, random_state=2)
    features = [c for c in df if c != "price"]
    save(RandomForestRegressor(n_estimators=20, max_depth=8, random_state=0).fit(train[features], train.price),
         "03_house_price_model.joblib")  # fmt: skip
    test.to_csv(HERE / "03_house_price_data.csv", index=False)


def loans() -> None:
    """Binary classification with a decision tree: loan approved or not."""
    rng = np.random.default_rng(11)
    n = 500
    df = pd.DataFrame(
        {
            "income_k": rng.normal(55, 18, n).round(1).clip(15),
            "credit_score": rng.normal(680, 60, n).round().clip(450, 850).astype(int),
            "loan_amount_k": rng.normal(25, 10, n).round(1).clip(2),
            "years_employed": rng.integers(0, 25, n),
        }
    )
    score = 0.04 * df.income_k + 0.012 * df.credit_score - 0.06 * df.loan_amount_k + 0.05 * df.years_employed
    df["approved"] = ((score + rng.normal(0, 0.9, n)) > score.median()).astype(int)
    train, test = train_test_split(df, test_size=0.3, random_state=3)
    features = [c for c in df if c != "approved"]
    save(DecisionTreeClassifier(max_depth=4, random_state=0).fit(train[features], train.approved), "04_loan_model.joblib")
    test.to_csv(HERE / "04_loan_data.csv", index=False)


def energy() -> None:
    """Regression with a plain linear model: daily energy use from the weather."""
    rng = np.random.default_rng(5)
    n = 300
    df = pd.DataFrame(
        {
            "temperature_c": rng.normal(12, 9, n).round(1),
            "humidity_pct": rng.uniform(30, 95, n).round(),
            "occupants": rng.integers(1, 7, n),
        }
    )
    df["energy_kwh"] = (30 - 0.9 * df.temperature_c + 0.05 * df.humidity_pct + 2.2 * df.occupants
                        + rng.normal(0, 1.5, n)).round(2)  # fmt: skip
    train, test = train_test_split(df, test_size=0.3, random_state=4)
    features = [c for c in df if c != "energy_kwh"]
    save(LinearRegression().fit(train[features], train.energy_kwh), "05_energy_model.joblib")
    test.to_csv(HERE / "05_energy_data.csv", index=False)


def cancer() -> None:
    """A real dataset (breast cancer, 30 features) with a scikit-learn Pipeline (scaler then logistic regression)."""
    frame = load_breast_cancer(as_frame=True).frame.rename(columns={"target": "diagnosis"})
    frame.columns = [c.replace(" ", "_") for c in frame.columns]
    train, test = train_test_split(frame, test_size=0.35, random_state=6, stratify=frame.diagnosis)
    features = [c for c in frame if c != "diagnosis"]
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(train[features], train.diagnosis)
    save(pipeline, "06_cancer_pipeline_model.joblib")
    test.to_csv(HERE / "06_cancer_data.csv", index=False)


# --- inputs the application should refuse, or fail clearly on ----------------------------------------------------


def bad_inputs() -> None:
    (HERE / "bad_ragged_rows.csv").write_text("tenure_months,monthly_charge,support_calls,contract_years,churned\n"
                                              "12,59.9,2,1,0\n30,70.5,1\n8,44.0,5,1,1,extra\n")  # fmt: skip
    (HERE / "bad_empty.csv").write_text("")
    (HERE / "bad_wrong_columns.csv").write_text("sepal_size,petal_size,colour,label\n1.2,3.4,red,0\n2.2,1.1,blue,1\n")
    (HERE / "bad_unsupported_model.txt").write_text("This is not a model file: only .joblib and .pkl are supported.\n")
    (HERE / "bad_corrupt_model.joblib").write_bytes(b"\x00\x01this is not a real model file\xff" * 8)
    joblib.dump({"name": "a dictionary, not a model"}, HERE / "bad_not_a_model.joblib")


# --- check what the application does with each ---------------------------------------------------------------------

GOOD = [
    ("01_churn_model.joblib", "01_churn_data.csv", "classification", "churned"),
    ("02_iris_model.pkl", "02_iris_data.csv", "classification", "species"),
    ("03_house_price_model.joblib", "03_house_price_data.csv", "regression", "price"),
    ("04_loan_model.joblib", "04_loan_data.csv", "classification", "approved"),
    ("05_energy_model.joblib", "05_energy_data.csv", "regression", "energy_kwh"),
    ("06_cancer_pipeline_model.joblib", "06_cancer_data.csv", "classification", "diagnosis"),
]
CASES = GOOD + [
    ("01_churn_model.joblib", "bad_ragged_rows.csv", "classification", "churned"),
    ("01_churn_model.joblib", "bad_empty.csv", "classification", "churned"),
    ("01_churn_model.joblib", "bad_wrong_columns.csv", "classification", "label"),
    ("01_churn_model.joblib", "01_churn_data.csv", "classification", "tenure_months"),  # a feature picked as the target
    ("bad_unsupported_model.txt", "01_churn_data.csv", "classification", "churned"),
    ("bad_corrupt_model.joblib", "01_churn_data.csv", "classification", "churned"),
    ("bad_not_a_model.joblib", "01_churn_data.csv", "classification", "churned"),
    ("01_churn_model.joblib", "01_churn_data.csv", "clustering", "churned"),
    ("01_churn_model.joblib", "01_churn_data.csv", "classification", "no_such_column"),
]


def verify() -> None:
    sys.path.insert(0, str(BACKEND))
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app

    client = TestClient(create_app(Settings(storage_dir=Path(tempfile.mkdtemp()) / "uploads")), raise_server_exceptions=False)
    for model, data, task, target in CASES:
        response = client.post(
            "/api/evaluations",
            data={"task_type": task, "target_column": target},
            files={"model": (model, (HERE / model).read_bytes()), "dataset": (data, (HERE / data).read_bytes())},
        )
        label = f"{model} + {data} ({task}, {target})"
        if response.status_code != 202:
            error = response.json()["error"]
            print(f"REJECTED {response.status_code} {error['code']}: {error['message'][:90]}\n         {label}")
            continue
        body = client.get(f"/api/evaluations/{response.json()['evaluation_id']}").json()
        if body["status"] == "completed":
            metrics = ", ".join(f"{k} {v:.4f}" for k, v in body["metrics"].items())
            print(f"COMPLETED {metrics}\n         {label}")
        else:
            print(f"FAILED    {body['error']['code']}: {body['error']['message'][:90]}\n         {label}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="also run every input through the application")
    args = parser.parse_args()
    for step in (churn, iris, houses, loans, energy, cancer, bad_inputs):
        step()
    print(f"wrote {len(list(HERE.glob('*.joblib'))) + len(list(HERE.glob('*.pkl')))} models and "
          f"{len(list(HERE.glob('*.csv')))} datasets to {HERE}")  # fmt: skip
    if args.verify:
        verify()


if __name__ == "__main__":
    main()
