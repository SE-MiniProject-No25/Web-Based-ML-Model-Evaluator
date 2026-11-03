"""Pre-flight check for the demo (EN-08): run every scenario in planning/Demo_Script.md against a live server.

    python scripts/demo_check.py                       # server on http://127.0.0.1:8000
    python scripts/demo_check.py --url http://127.0.0.1:8010

Each scenario prints PASS or FAIL with what the demo script says should happen. Run it right before a demo
or rehearsal; exit status 1 means something would have surprised you on stage.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
CLASSIFICATION = FIXTURES / "classification"
REGRESSION = FIXTURES / "regression"
NEGATIVE = FIXTURES / "negative"
CLF_MODEL, CLF_DATA = CLASSIFICATION / "model.joblib", CLASSIFICATION / "data.csv"
REG_MODEL, REG_DATA = REGRESSION / "model.joblib", REGRESSION / "data.csv"


def submit(client, model, dataset, task_type, target, model_name=None, dataset_name=None):
    return client.post(
        "/api/evaluations",
        data={"task_type": task_type, "target_column": target},
        files={
            "model": (model_name or model.name, model.read_bytes()),
            "dataset": (dataset_name or dataset.name, dataset.read_bytes()),
        },
    )


def wait_for_result(client, evaluation_id: str, timeout: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/api/evaluations/{evaluation_id}").json()
        if body["status"] in {"completed", "failed"}:
            return body
        time.sleep(0.5)
    raise TimeoutError("the evaluation did not finish in time")


def expected(folder: Path) -> dict:
    return json.loads((folder / "expected_metrics.json").read_text())


def close(actual: dict, wanted: dict) -> bool:
    return all(abs(actual.get(k, float("inf")) - v) < 1e-6 for k, v in wanted.items())


def run_checks(client) -> list[tuple[str, bool, str]]:
    results = []

    def record(name: str, ok: bool, detail: str):
        results.append((name, bool(ok), detail))

    # 1. Happy path (UC-01) and 2. download (UC-03)
    response = submit(client, CLF_MODEL, CLF_DATA, "classification", "label")
    evaluation_id = response.json().get("evaluation_id", "")
    record("UC-01 submit is accepted", response.status_code == 202, f"HTTP {response.status_code}")
    body = wait_for_result(client, evaluation_id)
    record(
        "UC-01 classification completes with the reference metrics",
        body["status"] == "completed" and close(body.get("metrics", {}), expected(CLASSIFICATION)),
        f"{body['status']}, accuracy {body.get('metrics', {}).get('accuracy')}",
    )
    download = client.get(f"/api/evaluations/{evaluation_id}/download")
    record(
        "UC-03 result downloads as a JSON file",
        download.status_code == 200
        and "attachment" in download.headers.get("content-disposition", "")
        and download.json().get("metrics") == body.get("metrics"),
        f"HTTP {download.status_code}, {download.headers.get('content-disposition', '')}",
    )

    # UC-01 regression
    response = submit(client, REG_MODEL, REG_DATA, "regression", "price")
    body = wait_for_result(client, response.json()["evaluation_id"])
    record(
        "UC-01 regression completes with the reference metrics",
        body["status"] == "completed" and close(body.get("metrics", {}), expected(REGRESSION)),
        f"{body['status']}, r2 {body.get('metrics', {}).get('r2')}",
    )

    # 3. Validation rejection (UC-02): a malformed CSV is refused before anything runs
    response = submit(client, CLF_MODEL, NEGATIVE / "malformed.csv", "classification", "label")
    record(
        "UC-02 malformed CSV is rejected (422 MALFORMED_DATASET)",
        response.status_code == 422 and response.json()["error"]["code"] == "MALFORMED_DATASET",
        f"HTTP {response.status_code} {response.json().get('error', {}).get('code')}",
    )

    # 4. A failed evaluation: columns that don't match the model
    response = submit(client, CLF_MODEL, NEGATIVE / "incompatible.csv", "classification", "label")
    accepted = response.status_code == 202
    body = wait_for_result(client, response.json()["evaluation_id"]) if accepted else {}
    error = body.get("error", {})
    record(
        "Failed evaluation: wrong columns end as INCOMPATIBLE_INPUTS and name the columns",
        accepted
        and body.get("status") == "failed"
        and error.get("code") == "INCOMPATIBLE_INPUTS"
        and "feature_a" in error.get("message", ""),
        f"{body.get('status')} {error.get('code')}",
    )

    # 5. Security rejections: wrong file type, a corrupt model, a path-like filename
    response = submit(client, NEGATIVE / "unsupported.txt", CLF_DATA, "classification", "label")
    record(
        "Security: an unsupported file type is rejected (415)",
        response.status_code == 415 and response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE",
        f"HTTP {response.status_code}",
    )
    response = submit(client, NEGATIVE / "malformed_model.joblib", CLF_DATA, "classification", "label")
    record(
        "Security: a corrupt model is rejected before it runs (422 INVALID_MODEL)",
        response.status_code == 422 and response.json()["error"]["code"] == "INVALID_MODEL",
        f"HTTP {response.status_code}",
    )
    response = submit(client, CLF_MODEL, CLF_DATA, "classification", "label", dataset_name="../../evil.csv")
    body = wait_for_result(client, response.json()["evaluation_id"]) if response.status_code == 202 else {}
    record(
        "Security: a path-like filename is handled safely (evaluates normally, nothing escapes)",
        response.status_code == 202 and body.get("status") == "completed",
        f"HTTP {response.status_code}, {body.get('status')}",
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="base URL of a running server")
    args = parser.parse_args()

    try:
        with httpx.Client(base_url=args.url, timeout=60.0) as client:
            results = run_checks(client)
    except httpx.ConnectError:
        print(f"Could not connect to {args.url}. Start the backend first (see the README).", file=sys.stderr)
        return 2

    width = max(len(name) for name, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} demo scenarios behave as scripted.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
