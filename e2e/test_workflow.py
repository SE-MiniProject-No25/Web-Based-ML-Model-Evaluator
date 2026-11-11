"""The main workflow in a real browser, against the real backend (TEST-07).

Replaces the manual interface checks of the System Validation Report (section 6). Covers TC-01, TC-02,
TC-07 (the interface half), TC-08, TC-09, TC-11 and TC-12.

    pip install -r e2e/requirements.txt && python -m playwright install chromium
    cd frontend && npm install && cd ..
    python -m pytest e2e
"""

import json
import re

from playwright.sync_api import Page, expect

from e2e.conftest import DEMO_INPUTS


def choose_files(page: Page, model: str, dataset: str) -> None:
    page.locator("input[type=file]").nth(0).set_input_files(DEMO_INPUTS / model)
    page.locator("input[type=file]").nth(1).set_input_files(DEMO_INPUTS / dataset)


def run(page: Page, model: str, dataset: str, task: str, target: str) -> None:
    choose_files(page, model, dataset)
    page.get_by_role("button", name="Next: Configure").click()
    page.locator("select").nth(0).select_option(task)
    page.locator("select").nth(1).select_option(target)
    page.get_by_role("button", name="Next: Review").click()
    page.get_by_role("button", name="Evaluate model").click()


def test_a_classification_run_shows_the_metrics_table_and_chart(page: Page):
    run(page, "01_churn_model.joblib", "01_churn_data.csv", "classification", "churned")

    expect(page.get_by_text("COMPLETED", exact=True)).to_be_visible()
    table = page.get_by_role("table")
    expected = (("Accuracy", "0.7444"), ("Precision", "0.7416"), ("Recall", "0.7416"), ("F1-score", "0.7416"))
    for label, value in expected:
        expect(table.get_by_role("row", name=re.compile(rf"^{re.escape(label)} "))).to_contain_text(value)
    expect(table).to_contain_text("The share of predictions that were correct")
    expect(page.get_by_role("img", name="Accuracy: 0.7444")).to_be_visible()


def test_a_regression_run_shows_its_own_metrics(page: Page):
    run(page, "03_house_price_model.joblib", "03_house_price_data.csv", "regression", "price")

    expect(page.get_by_text("COMPLETED", exact=True)).to_be_visible()
    table = page.get_by_role("table")
    for label, value in (("MAE", "29.1741"), ("RMSE", "35.6048"), ("R²", "0.8965")):
        expect(table.get_by_role("row", name=re.compile(rf"^{re.escape(label)} "))).to_contain_text(value)


def test_the_result_downloads_as_a_json_file(page: Page, tmp_path):
    run(page, "01_churn_model.joblib", "01_churn_data.csv", "classification", "churned")
    expect(page.get_by_text("COMPLETED", exact=True)).to_be_visible()

    with page.expect_download() as download:
        page.get_by_role("button", name="Download Results").click()

    assert download.value.suggested_filename.startswith("evaluation-")
    saved = tmp_path / download.value.suggested_filename
    download.value.save_as(saved)
    result = json.loads(saved.read_text(encoding="utf-8"))
    assert result["status"] == "completed"
    assert result["target_column"] == "churned"
    assert round(result["metrics"]["accuracy"], 4) == 0.7444


def test_a_malformed_csv_is_rejected_and_shown_next_to_the_dataset(page: Page):
    run(page, "01_churn_model.joblib", "bad_ragged_rows.csv", "classification", "churned")

    expect(page.get_by_text("ragged rows with inconsistent column counts")).to_be_visible()
    expect(page.locator("input[type=file]").nth(1)).to_have_attribute("aria-invalid", "true")
    expect(page.get_by_role("button", name="Download Results")).to_have_count(0)


def test_a_mismatched_dataset_fails_and_names_the_columns(page: Page):
    run(page, "01_churn_model.joblib", "01_churn_data.csv", "classification", "tenure_months")

    expect(page.get_by_text("FAILED", exact=True)).to_be_visible()
    message = "Missing from the dataset: tenure_months. Not used by the model: churned."
    expect(page.get_by_text(message)).to_be_visible()
    expect(page.get_by_role("button", name="Download Results")).to_have_count(0)


def test_an_unsupported_model_file_is_refused_on_selection(page: Page):
    page.locator("input[type=file]").nth(0).set_input_files(DEMO_INPUTS / "bad_unsupported_model.txt")

    expect(page.get_by_text("Please select a .pkl or .joblib model file.")).to_be_visible()
    expect(page.get_by_role("button", name="Next: Configure")).to_be_disabled()


def test_an_unreachable_backend_is_reported(page: Page):
    page.route("**/api/**", lambda route: route.abort())  # as if the backend were down
    run(page, "01_churn_model.joblib", "01_churn_data.csv", "classification", "churned")

    expect(page.get_by_text("Unable to connect to the evaluation server")).to_be_visible()
