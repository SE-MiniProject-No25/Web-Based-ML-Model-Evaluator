"""OpenAPI documentation for the evaluation endpoints (Architecture sections 10 and 11).

Only documentation lives here; no behaviour. The examples are the messages the API really returns,
and tests/test_openapi.py checks that every error code in the Architecture table is documented.
"""

EXAMPLE_ID = "3f2b8c1e-9d4a-4e6b-8a57-1c2d3e4f5a6b"

API_DESCRIPTION = """\
Evaluate a scikit-learn model against a CSV dataset and read the standard metrics.

**Workflow:** `POST /api/evaluations` to submit (answered at once with `202`), poll
`GET /api/evaluations/{id}` until `status` is `completed` or `failed`, then optionally
`GET /api/evaluations/{id}/download` for the result as a file.

**Errors** always have the form `{"error": {"code": "...", "message": "..."}}` and never contain stack
traces or server paths. Errors that happen *after* the `202` (`INCOMPATIBLE_INPUTS`,
`RESOURCE_LIMIT_EXCEEDED`, `EVALUATION_FAILED`) are not HTTP errors: the evaluation's status becomes
`failed` and the same `error` object is returned by the status endpoint.

**Authentication is optional and off by default.** Set `MLEVAL_AUTH_ENABLED=true` and `MLEVAL_API_KEY` to
switch it on; then send the key in the `X-API-Key` header or as `Authorization: Bearer <key>`. A request
without a valid key is answered with `401 UNAUTHENTICATED`. `/api/health` stays open.

Every error uses the format above, including unknown URLs (`404 NOT_FOUND`), unsupported methods
(`405 METHOD_NOT_ALLOWED`) and unexpected server errors (`500 INTERNAL_SERVER_ERROR`).
"""

TAGS = [{"name": "evaluations", "description": "Submit an evaluation, follow it, and download its result."}]


def _example(code: str, message: str) -> dict:
    return {"summary": code, "value": {"error": {"code": code, "message": message}}}


def error_response(description: str, **examples: str) -> dict:
    """An OpenAPI response entry for an error status; ``examples`` maps error code -> sample message."""
    return {
        "description": description,
        "content": {
            "application/json": {"examples": {code: _example(code, message) for code, message in examples.items()}}
        },
    }


UNAUTHENTICATED = error_response(
    "Authentication is enabled and the request has no valid API key (`X-API-Key` or `Authorization: Bearer`).",
    UNAUTHENTICATED="Authentication is required.",
)

NOT_FOUND = error_response(
    "No evaluation has this ID.",
    EVALUATION_NOT_FOUND="Evaluation not found.",
)

SUBMIT_RESPONSES = {
    202: {
        "description": "Accepted. The evaluation was created and runs in the background; poll the status endpoint.",
        "content": {
            "application/json": {"example": {"evaluation_id": EXAMPLE_ID, "status": "pending"}},
        },
    },
    400: error_response(
        "A required field is missing. The message names the missing fields.",
        MISSING_REQUIRED_FIELD="Missing required field(s): dataset, target_column.",
    ),
    401: UNAUTHENTICATED,
    413: error_response(
        "A file is larger than the configured upload limit (default 10 MB).",
        FILE_TOO_LARGE="The model file exceeds the maximum allowed size of 10485760 bytes.",
    ),
    415: error_response(
        "A file has an unsupported type. Models: .joblib or .pkl. Datasets: .csv.",
        UNSUPPORTED_FILE_TYPE="The model must be one of: .joblib, .pkl.",
    ),
    422: error_response(
        "The inputs are present but invalid. Nothing is stored and no evaluation is created.",
        MALFORMED_DATASET="The dataset file is empty.",
        INVALID_MODEL="The model file could not be loaded or is corrupted.",
        INVALID_TARGET_COLUMN="The selected target column 'price' does not exist in the dataset.",
        INVALID_TASK_TYPE="The task type must be one of: classification, regression.",
    ),
}

STATUS_RESPONSES = {
    200: {
        "description": (
            "The evaluation's current state. `pending` and `running` have only `evaluation_id` and `status`. "
            "`completed` adds `task_type` and `metrics`. `failed` adds `task_type` and `error` instead of metrics."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "pending": {"value": {"evaluation_id": EXAMPLE_ID, "status": "pending"}},
                    "running": {"value": {"evaluation_id": EXAMPLE_ID, "status": "running"}},
                    "completed (classification)": {
                        "value": {
                            "evaluation_id": EXAMPLE_ID,
                            "status": "completed",
                            "task_type": "classification",
                            "metrics": {"accuracy": 0.94, "precision": 0.93, "recall": 0.92, "f1": 0.925},
                        }
                    },
                    "completed (regression)": {
                        "value": {
                            "evaluation_id": EXAMPLE_ID,
                            "status": "completed",
                            "task_type": "regression",
                            "metrics": {"mae": 24.5, "mse": 970.1, "rmse": 31.1, "r2": 0.92},
                        }
                    },
                    "failed: INCOMPATIBLE_INPUTS": {
                        "value": {
                            "evaluation_id": EXAMPLE_ID,
                            "status": "failed",
                            "task_type": "classification",
                            "error": {
                                "code": "INCOMPATIBLE_INPUTS",
                                "message": (
                                    "The dataset's columns do not match the features the model expects. "
                                    "Missing from the dataset: tenure_months. Not used by the model: churned."
                                ),
                            },
                        }
                    },
                    "failed: RESOURCE_LIMIT_EXCEEDED": {
                        "value": {
                            "evaluation_id": EXAMPLE_ID,
                            "status": "failed",
                            "task_type": "classification",
                            "error": {
                                "code": "RESOURCE_LIMIT_EXCEEDED",
                                "message": "The evaluation exceeded the time limit of 60 seconds and was stopped.",
                            },
                        }
                    },
                    "failed: EVALUATION_FAILED": {
                        "value": {
                            "evaluation_id": EXAMPLE_ID,
                            "status": "failed",
                            "task_type": "classification",
                            "error": {
                                "code": "EVALUATION_FAILED",
                                "message": "The evaluation could not be completed.",
                            },
                        }
                    },
                }
            }
        },
    },
    401: UNAUTHENTICATED,
    404: NOT_FOUND,
}

DOWNLOAD_RESPONSES = {
    200: {
        "description": (
            "The completed result as a JSON file "
            '(`Content-Disposition: attachment; filename="evaluation-<id>.json"`).'
        ),
        "content": {
            "application/json": {
                "example": {
                    "evaluation_id": EXAMPLE_ID,
                    "status": "completed",
                    "task_type": "classification",
                    "target_column": "churned",
                    "model_filename": "churn_classifier.joblib",
                    "dataset_filename": "churn_dataset.csv",
                    "metrics": {"accuracy": 0.94, "precision": 0.93, "recall": 0.92, "f1": 0.925},
                    "created_at": "2026-11-03T12:00:00.123456+00:00",
                    "finished_at": "2026-11-03T12:00:03.456789+00:00",
                }
            }
        },
    },
    401: UNAUTHENTICATED,
    404: NOT_FOUND,
    409: error_response(
        "The evaluation has not completed (still pending or running, or it failed), so there is no result file.",
        EVALUATION_NOT_COMPLETED="The evaluation has not finished yet. Try again when its status is completed.",
    ),
}

FIELD_DESCRIPTIONS = {
    "model": "The trained model: a scikit-learn model saved with joblib (`.joblib` or `.pkl`). Required.",
    "dataset": "The evaluation data as a CSV file with a header row (`.csv`). Required.",
    "task_type": "`classification` or `regression`. Required.",
    "target_column": "The dataset column the model predicts; it must exist in the CSV header. Required.",
}
