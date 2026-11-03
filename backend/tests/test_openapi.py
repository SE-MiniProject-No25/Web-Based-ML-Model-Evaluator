"""EN-07: the running API documents exactly the contract in Architecture sections 10 and 11."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.errors import HTTP_STATUS, ErrorCode
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures" / "classification"

# Architecture 10.1 - 10.3: the HTTP statuses each endpoint lists.
EXPECTED_STATUSES = {
    ("post", "/api/evaluations"): {"202", "400", "401", "413", "415", "422"},
    ("get", "/api/evaluations/{evaluation_id}"): {"200", "401", "404"},
    ("get", "/api/evaluations/{evaluation_id}/download"): {"200", "401", "404", "409"},
}


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


@pytest.fixture
def spec(client):
    return client.get("/openapi.json").json()


def documented_error_codes(operation):
    """{http status: [error codes documented for it]} for one operation."""
    found = {}
    for status, response in operation["responses"].items():
        examples = response.get("content", {}).get("application/json", {}).get("examples", {})
        codes = [e["value"]["error"]["code"] for e in examples.values() if "error" in e.get("value", {})]
        if codes:
            found[status] = codes
    return found


def test_interactive_docs_are_served(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert client.get("/openapi.json").status_code == 200


def test_every_endpoint_from_the_architecture_is_listed(spec):
    for (method, path), statuses in EXPECTED_STATUSES.items():
        assert method in spec["paths"][path], f"{method.upper()} {path} is not documented"
        assert set(spec["paths"][path][method]["responses"]) >= statuses


def test_the_submit_request_fields_are_documented(spec):
    body = spec["paths"]["/api/evaluations"]["post"]["requestBody"]["content"]["multipart/form-data"]
    schema = spec["components"]["schemas"][body["schema"]["$ref"].split("/")[-1]]
    assert set(schema["properties"]) == {"model", "dataset", "task_type", "target_column"}
    for name, definition in schema["properties"].items():
        text = json.dumps(definition)
        assert "description" in text, f"field {name} has no description"


def test_every_error_code_in_the_architecture_table_is_documented(spec):
    text = json.dumps(spec)
    for code in ErrorCode:
        assert f'"{code.value}"' in text, f"{code.value} is missing from the API documentation"


def test_documented_error_codes_sit_under_the_http_status_the_api_uses(spec):
    checked = 0
    for (method, path) in EXPECTED_STATUSES:
        for status, codes in documented_error_codes(spec["paths"][path][method]).items():
            if status == "200":  # failures that happen after the 202 live inside a 200 status response
                continue
            for code in codes:
                assert HTTP_STATUS[ErrorCode(code)] == int(status), f"{code} documented under {status}"
                checked += 1
    assert checked >= 10


def test_errors_after_the_202_are_documented_on_the_status_endpoint(spec):
    examples = spec["paths"]["/api/evaluations/{evaluation_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]
    failed_codes = {e["value"]["error"]["code"] for e in examples.values() if "error" in e["value"]}
    assert failed_codes == {"INCOMPATIBLE_INPUTS", "RESOURCE_LIMIT_EXCEEDED", "EVALUATION_FAILED"}
    assert all(HTTP_STATUS[ErrorCode(c)] is None for c in failed_codes)


def test_documented_examples_have_exactly_the_keys_of_the_real_responses(client, spec):
    """The examples are written by hand, so make sure they cannot drift from what the API returns."""
    submitted = client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={
            "model": ("model.joblib", (FIXTURES / "model.joblib").read_bytes()),
            "dataset": ("data.csv", (FIXTURES / "data.csv").read_bytes()),
        },
    )
    evaluation_id = submitted.json()["evaluation_id"]
    status = client.get(f"/api/evaluations/{evaluation_id}").json()
    download = client.get(f"/api/evaluations/{evaluation_id}/download").json()

    paths = spec["paths"]
    accepted = paths["/api/evaluations"]["post"]["responses"]["202"]["content"]["application/json"]["example"]
    completed = paths["/api/evaluations/{evaluation_id}"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]["completed (classification)"]["value"]
    file_example = paths["/api/evaluations/{evaluation_id}/download"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]

    assert set(accepted) == set(submitted.json())
    assert set(completed) == set(status)
    assert set(completed["metrics"]) == set(status["metrics"])
    assert set(file_example) == set(download)
