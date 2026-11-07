"""Tests for Optional API Authentication (US-11, US-28 / Issue #30, TC-17).

Requirements covered:
- NFR-07: Protect evaluation endpoints against unauthenticated access when enabled.
- SEC-05: Error messages must never contain secrets or internal details.
- SEC-06: Enforce configured authentication on evaluation and result endpoints.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api.auth import extract_credentials, is_protected_path, verify_api_key
from app.config import Settings
from app.errors import ErrorCode
from app.main import create_app
from app.results import InMemoryEvaluationStore, ResultService
from tests.helpers import write_classification_fixture

TEST_KEY = "mleval-test-secret-key-12345"


@pytest.fixture
def auth_settings(tmp_path):
    """Settings with authentication enabled and a known test API key."""
    return Settings(
        auth_enabled=True,
        api_key=TEST_KEY,
        storage_dir=tmp_path / "uploads",
    )


@pytest.fixture
def store():
    return InMemoryEvaluationStore()


@pytest.fixture
def auth_client(auth_settings, store):
    """TestClient with authentication enabled."""
    app = create_app(auth_settings, ResultService(store))
    return TestClient(app)


def _submit_classification(client, tmp_path, headers=None, **form_overrides):
    """Helper to POST an evaluation with minimal fixtures."""
    model_path, dataset_path = write_classification_fixture(tmp_path / "fixtures")
    fields = {"task_type": "classification", "target_column": "label", **form_overrides}
    files = {
        "model": (model_path.name, model_path.read_bytes()),
        "dataset": (dataset_path.name, dataset_path.read_bytes()),
    }
    return client.post("/api/evaluations", data=fields, files=files, headers=headers)


# ---------------------------------------------------------------------------
# Section A: Authentication Disabled (Default Behavior)
# ---------------------------------------------------------------------------


def test_auth_is_disabled_by_default():
    """Authentication must be disabled by default (US-11 acceptance criteria)."""
    settings = Settings()
    assert settings.auth_enabled is False
    assert settings.api_key is None


def test_disabled_auth_allows_post_without_credentials(client, tmp_path):
    """TC-17 / NFR-07: Endpoints function normally without credentials when disabled."""
    response = _submit_classification(client, tmp_path)
    assert response.status_code == 202
    assert "evaluation_id" in response.json()
    assert response.json()["status"] == "pending"


def test_disabled_auth_allows_get_without_credentials(client):
    """GET /api/evaluations/{id} works without credentials when auth is disabled."""
    response = client.get("/api/evaluations/eval_missing")
    # Returns 404 EVALUATION_NOT_FOUND, not 401 UNAUTHENTICATED
    assert response.status_code == 404
    assert response.json()["error"]["code"] == ErrorCode.EVALUATION_NOT_FOUND.value


def test_disabled_auth_permits_requests_with_arbitrary_credentials(client, tmp_path):
    """When disabled, passing credentials does not block or break the request."""
    response = _submit_classification(
        client,
        tmp_path,
        headers={"X-API-Key": "random-key", "Authorization": "Bearer random-token"},
    )
    assert response.status_code == 202


def test_disabled_auth_health_check(client):
    """Health check is accessible when authentication is disabled."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Section B: Authentication Enabled - Credential Verification & Lifecycle
# ---------------------------------------------------------------------------


def test_valid_x_api_key_header_post(auth_client, tmp_path):
    """TC-17: Valid X-API-Key header successfully authenticates POST /api/evaluations."""
    response = _submit_classification(auth_client, tmp_path, headers={"X-API-Key": TEST_KEY})
    assert response.status_code == 202
    assert "evaluation_id" in response.json()


def test_valid_authorization_bearer_header_post(auth_client, tmp_path):
    """TC-17: Valid Authorization: Bearer <key> successfully authenticates POST /api/evaluations."""
    response = _submit_classification(
        auth_client,
        tmp_path,
        headers={"Authorization": f"Bearer {TEST_KEY}"},
    )
    assert response.status_code == 202
    assert "evaluation_id" in response.json()


def test_authenticated_get_existing_evaluation_returns_200(auth_client):
    """Authenticated GET /api/evaluations/{id} returns 200 with status for an existing record."""
    # Seed an evaluation record in results
    results = auth_client.app.state.results
    eval_rec = results.create(
        task_type="classification",
        target_column="label",
        model_filename="model.joblib",
        dataset_filename="data.csv",
        model_path="dummy_model",
        dataset_path="dummy_data",
    )
    eval_id = eval_rec.id

    # 1. Authenticated via X-API-Key
    res_x_api = auth_client.get(
        f"/api/evaluations/{eval_id}",
        headers={"X-API-Key": TEST_KEY},
    )
    assert res_x_api.status_code == 200
    assert res_x_api.json()["evaluation_id"] == eval_id
    assert res_x_api.json()["status"] == "pending"

    # 2. Authenticated via Authorization: Bearer
    res_bearer = auth_client.get(
        f"/api/evaluations/{eval_id}",
        headers={"Authorization": f"Bearer {TEST_KEY}"},
    )
    assert res_bearer.status_code == 200
    assert res_bearer.json()["evaluation_id"] == eval_id
    assert res_bearer.json()["status"] == "pending"


def test_header_case_insensitivity(auth_client, tmp_path):
    """HTTP header names and Bearer scheme prefix are handled case-insensitively."""
    # Lowercase header name and lowercase scheme
    res1 = _submit_classification(
        auth_client,
        tmp_path,
        headers={"authorization": f"bearer {TEST_KEY}"},
    )
    assert res1.status_code == 202

    # Lowercase X-API-Key header name
    res2 = _submit_classification(
        auth_client,
        tmp_path,
        headers={"x-api-key": TEST_KEY},
    )
    assert res2.status_code == 202

    # Uppercase BEARER prefix
    res3 = _submit_classification(
        auth_client,
        tmp_path,
        headers={"Authorization": f"BEARER {TEST_KEY}"},
    )
    assert res3.status_code == 202


def test_missing_credentials_rejected_with_401(auth_client):
    """TC-17 / SEC-06: Protected endpoint rejects request missing credentials with 401."""
    response = auth_client.get("/api/evaluations/eval_123")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "UNAUTHENTICATED",
            "message": "Authentication required.",
        }
    }


def test_invalid_and_missing_credentials_return_401_for_both_get_and_post(auth_client, tmp_path):
    """Both GET and POST on protected endpoints reject missing or invalid credentials with 401."""
    # 1. GET missing credentials
    r1 = auth_client.get("/api/evaluations/eval_123")
    assert r1.status_code == 401
    assert r1.json()["error"]["code"] == "UNAUTHENTICATED"

    # 2. GET invalid X-API-Key
    r2 = auth_client.get("/api/evaluations/eval_123", headers={"X-API-Key": "wrong"})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "UNAUTHENTICATED"

    # 3. GET invalid Bearer token
    r3 = auth_client.get("/api/evaluations/eval_123", headers={"Authorization": "Bearer wrong"})
    assert r3.status_code == 401
    assert r3.json()["error"]["code"] == "UNAUTHENTICATED"

    # 4. POST missing credentials
    r4 = _submit_classification(auth_client, tmp_path, headers=None)
    assert r4.status_code == 401
    assert r4.json()["error"]["code"] == "UNAUTHENTICATED"

    # 5. POST invalid X-API-Key
    r5 = _submit_classification(auth_client, tmp_path, headers={"X-API-Key": "wrong"})
    assert r5.status_code == 401
    assert r5.json()["error"]["code"] == "UNAUTHENTICATED"

    # 6. POST invalid Bearer token
    r6 = _submit_classification(auth_client, tmp_path, headers={"Authorization": "Bearer wrong"})
    assert r6.status_code == 401
    assert r6.json()["error"]["code"] == "UNAUTHENTICATED"


def test_dual_authentication_headers(auth_client, tmp_path):
    """Test behavior when both X-API-Key and Authorization: Bearer headers are provided."""
    # Case 1: Both headers valid -> success (202)
    res_both_valid = _submit_classification(
        auth_client,
        tmp_path,
        headers={"X-API-Key": TEST_KEY, "Authorization": f"Bearer {TEST_KEY}"},
    )
    assert res_both_valid.status_code == 202

    # Case 2: Valid X-API-Key + invalid Bearer -> success (202)
    res_x_valid = _submit_classification(
        auth_client,
        tmp_path,
        headers={"X-API-Key": TEST_KEY, "Authorization": "Bearer wrong-token"},
    )
    assert res_x_valid.status_code == 202

    # Case 3: Invalid X-API-Key + valid Bearer -> success (202)
    res_bearer_valid = _submit_classification(
        auth_client,
        tmp_path,
        headers={"X-API-Key": "wrong-key", "Authorization": f"Bearer {TEST_KEY}"},
    )
    assert res_bearer_valid.status_code == 202

    # Case 4: Both headers invalid -> rejected (401)
    res_both_invalid = _submit_classification(
        auth_client,
        tmp_path,
        headers={"X-API-Key": "wrong-key", "Authorization": "Bearer wrong-token"},
    )
    assert res_both_invalid.status_code == 401
    assert res_both_invalid.json()["error"]["code"] == "UNAUTHENTICATED"


def test_non_ascii_credentials_do_not_raise_error(auth_client, tmp_path):
    """Non-ASCII candidate keys or configured keys must not raise TypeError or HTTP 500."""
    # 1. Non-ASCII invalid key sent as UTF-8 bytes to ASCII-configured server -> 401 (no 500)
    res_unicode = auth_client.get(
        "/api/evaluations/eval_123",
        headers={"X-API-Key": "clé_secrète_🔑".encode()},
    )
    assert res_unicode.status_code == 401
    assert res_unicode.json()["error"]["code"] == "UNAUTHENTICATED"

    # 2. Server configured with non-ASCII key
    unicode_key = "clé_secrète_🔑_évaluation"
    settings = Settings(auth_enabled=True, api_key=unicode_key, storage_dir=tmp_path)
    unicode_client = TestClient(create_app(settings))

    # Correct non-ASCII key authenticates successfully
    res_valid = unicode_client.get(
        "/api/evaluations/eval_123",
        headers={"X-API-Key": unicode_key.encode()},
    )
    assert res_valid.status_code == 404  # 404 means auth passed; record not found

    # Incorrect non-ASCII key rejected safely with 401
    res_invalid = unicode_client.get(
        "/api/evaluations/eval_123",
        headers={"X-API-Key": "clé_erronée_⛔".encode()},
    )
    assert res_invalid.status_code == 401
    assert res_invalid.json()["error"]["code"] == "UNAUTHENTICATED"


def test_duplicate_headers_handled_safely(auth_settings, store):
    """Duplicate X-API-Key or Authorization headers are evaluated without errors."""
    # Case 1: Duplicate X-API-Key where one is valid
    scope_x_valid = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [
            (b"x-api-key", b"wrong-key-1"),
            (b"x-api-key", TEST_KEY.encode()),
        ],
    }
    assert verify_api_key(Request(scope_x_valid), TEST_KEY) is True

    # Case 2: Duplicate X-API-Key where all are invalid
    scope_x_invalid = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [
            (b"x-api-key", b"wrong-key-1"),
            (b"x-api-key", b"wrong-key-2"),
        ],
    }
    assert verify_api_key(Request(scope_x_invalid), TEST_KEY) is False

    # Case 3: Duplicate Authorization where one is valid
    scope_auth_valid = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [
            (b"authorization", b"Bearer wrong-token"),
            (b"authorization", f"Bearer {TEST_KEY}".encode()),
        ],
    }
    assert verify_api_key(Request(scope_auth_valid), TEST_KEY) is True

    # Case 4: Duplicate Authorization where all are invalid
    scope_auth_invalid = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [
            (b"authorization", b"Bearer wrong-token-1"),
            (b"authorization", b"Bearer wrong-token-2"),
        ],
    }
    assert verify_api_key(Request(scope_auth_invalid), TEST_KEY) is False


@pytest.mark.parametrize(
    "bad_headers",
    [
        {"X-API-Key": ""},
        {"X-API-Key": "   "},
        {"Authorization": ""},
        {"Authorization": "   "},
        {"Authorization": "Bearer "},
        {"Authorization": "Bearer    "},
        {"Authorization": "Bearer"},
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Token some-token"},
        {"Authorization": "Digest username=foo"},
    ],
)
def test_malformed_credentials_rejected_with_401(auth_client, bad_headers):
    """Malformed, empty, or unsupported authorization headers are rejected."""
    response = auth_client.get("/api/evaluations/eval_123", headers=bad_headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_fail_secure_when_auth_enabled_but_no_key_configured(tmp_path):
    """Fail-secure: If auth is enabled but api_key is None, all requests are rejected."""
    settings = Settings(auth_enabled=True, api_key=None, storage_dir=tmp_path)
    client = TestClient(create_app(settings))

    # Even if client sends a key, request must fail because no valid server key is configured
    res1 = client.get("/api/evaluations/eval_123", headers={"X-API-Key": "any-key"})
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "UNAUTHENTICATED"

    # Request without headers must also fail
    res2 = client.get("/api/evaluations/eval_123")
    assert res2.status_code == 401


def test_fail_secure_when_auth_enabled_with_empty_or_whitespace_key(tmp_path):
    """Fail-secure: If auth is enabled but api_key is empty/whitespace, all requests are rejected."""
    for empty_key in ("", "   ", "\t\n"):
        settings = Settings(auth_enabled=True, api_key=empty_key, storage_dir=tmp_path)
        client = TestClient(create_app(settings))

        res = client.get("/api/evaluations/eval_123", headers={"X-API-Key": empty_key})
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "UNAUTHENTICATED"


# ---------------------------------------------------------------------------
# Section C: Endpoint Protection Scope and Path Normalization
# ---------------------------------------------------------------------------


def test_health_endpoint_remains_unauthenticated_when_auth_enabled(auth_client):
    """/api/health must remain publicly accessible without credentials."""
    response = auth_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_path_normalization_prevents_security_bypasses():
    """Path normalization prevents dot-dot traversal, URL encoding, and multi-slash bypasses."""
    # 1. URL percent encoding of 'e' (%65)
    assert is_protected_path("/api/%65valuations") is True
    # 2. Dot-dot traversal attempt from health to evaluations
    assert is_protected_path("/api/health/../evaluations") is True
    assert is_protected_path("/api/health/../evaluations/eval_123") is True
    # 3. Multiple leading or internal slashes
    assert is_protected_path("//api//evaluations") is True
    assert is_protected_path("///api///evaluations///123") is True
    # 4. Trailing slashes
    assert is_protected_path("/api/evaluations/") is True
    assert is_protected_path("/api/evaluations/eval_123/") is True

    # Non-evaluation paths must not be accidentally protected
    assert is_protected_path("/api/evaluations_other") is False
    assert is_protected_path("/api/health") is False
    assert is_protected_path("/api/health/") is False
    assert is_protected_path("/docs") is False
    assert is_protected_path("/openapi.json") is False
    assert is_protected_path("/") is False
    assert is_protected_path("") is False


def test_encoded_slashes_and_backslashes_in_path():
    """Paths with encoded slashes, backslashes, and %5C are normalized safely."""
    # Protected paths
    assert is_protected_path("/api%2Fevaluations") is True
    assert is_protected_path("/api%2fevaluations") is True
    assert is_protected_path(r"/api\evaluations") is True
    assert is_protected_path(r"/api\evaluations\123") is True
    assert is_protected_path("/api%5Cevaluations") is True
    assert is_protected_path("/api%5cevaluations") is True
    assert is_protected_path("/api%2Fevaluations%2F123") is True

    # Unprotected paths
    assert is_protected_path(r"/api\health") is False
    assert is_protected_path("/api%2Fhealth") is False
    assert is_protected_path("/api%5Chealth") is False


def test_future_download_endpoint_compatibility(auth_settings, store):
    """Verify that future subpaths like /download are protected and work with credentials."""
    app = create_app(auth_settings, ResultService(store))

    # Mount a mock download endpoint simulating PR #48
    @app.get("/api/evaluations/{evaluation_id}/download")
    def download_evaluation(evaluation_id: str):
        return {"download": True, "evaluation_id": evaluation_id}

    client = TestClient(app)

    # 1. Unauthenticated request to /download is rejected
    res_unauth = client.get("/api/evaluations/eval_123/download")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["error"]["code"] == "UNAUTHENTICATED"

    # 2. Authenticated request to /download succeeds
    res_auth = client.get(
        "/api/evaluations/eval_123/download",
        headers={"X-API-Key": TEST_KEY},
    )
    assert res_auth.status_code == 200
    assert res_auth.json() == {"download": True, "evaluation_id": "eval_123"}


# ---------------------------------------------------------------------------
# Section D: Security and Information Leakage Tests
# ---------------------------------------------------------------------------


def test_secrets_never_appear_in_error_responses(auth_client):
    """SEC-05: API keys must never appear in response bodies or response headers."""
    invalid_key = "attacker-probed-secret-999"
    response = auth_client.get(
        "/api/evaluations/eval_123",
        headers={"X-API-Key": invalid_key},
    )
    assert response.status_code == 401

    body_text = response.text
    assert TEST_KEY not in body_text
    assert invalid_key not in body_text

    # Header values must not echo the client's provided key
    for _, header_value in response.headers.items():
        assert TEST_KEY not in header_value
        assert invalid_key not in header_value


def test_api_keys_never_written_to_application_logs(auth_client, caplog):
    """SEC-05: Credentials must never be logged in application logs."""
    invalid_key = "unauthorized-secret-leak-test"
    with caplog.at_level(logging.DEBUG):
        # 1. Unauthenticated request with invalid key
        auth_client.get(
            "/api/evaluations/eval_123",
            headers={"X-API-Key": invalid_key},
        )
        # 2. Authenticated request with valid key
        auth_client.get(
            "/api/evaluations/eval_123",
            headers={"X-API-Key": TEST_KEY},
        )

    log_text = caplog.text
    assert TEST_KEY not in log_text
    assert invalid_key not in log_text


def test_unauthenticated_request_does_not_execute_endpoint_processing(
    auth_client, store, auth_settings
):
    """Authentication must execute BEFORE evaluation submission, file parsing, or storage."""
    # Send an unauthenticated request with completely invalid form fields
    response = auth_client.post(
        "/api/evaluations",
        data={"task_type": "invalid_task_type", "target_column": "missing"},
    )
    # Must be rejected with 401 UNAUTHENTICATED, NOT 400 or 422
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"

    # Verify no evaluation record was created in the result store
    assert len(store._records) == 0

    # Verify no files were stored in the storage directory
    if auth_settings.storage_dir.exists():
        assert len(list(auth_settings.storage_dir.iterdir())) == 0


def test_unauthenticated_post_with_oversized_file_rejected_early(auth_client, auth_settings):
    """Oversized files without credentials return 401 before file size checks or storage."""
    oversized_data = b"0" * (11 * 1024 * 1024)  # 11MB exceeds default 10MB limit
    response = auth_client.post(
        "/api/evaluations",
        data={"task_type": "classification", "target_column": "label"},
        files={"model": ("model.joblib", oversized_data)},
    )
    # Returns 401 UNAUTHENTICATED, NOT 413 FILE_TOO_LARGE
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"

    # No files stored
    if auth_settings.storage_dir.exists():
        assert len(list(auth_settings.storage_dir.iterdir())) == 0


def test_constant_time_comparison_is_used():
    """Verify secrets.compare_digest is used for constant-time credential comparison."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [(b"x-api-key", b"test-key")],
    }
    req = Request(scope)

    with patch("app.api.auth.secrets.compare_digest", return_value=True) as mock_compare:
        result = verify_api_key(req, "test-key")
        assert result is True
        assert mock_compare.called
        # Verify arguments passed to compare_digest
        mock_compare.assert_any_call(b"test-key", b"test-key")


def test_extract_credentials_helper():
    """Verify extract_credentials correctly parses supported headers."""
    # Both headers present
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [
            (b"x-api-key", b"key1"),
            (b"authorization", b"Bearer key2"),
        ],
    }
    req = Request(scope)
    extracted = extract_credentials(req)
    assert "key1" in extracted
    assert "key2" in extracted

    # No headers present
    empty_scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/evaluations",
        "headers": [],
    }
    empty_req = Request(empty_scope)
    assert extract_credentials(empty_req) == []


def test_concurrent_requests_handled_safely(auth_client):
    """Verify concurrent requests with mixed valid and invalid credentials have no race conditions."""
    def _send_request(idx: int) -> tuple[int, int]:
        is_valid = idx % 2 == 0
        headers = {"X-API-Key": TEST_KEY if is_valid else f"wrong-key-{idx}"}
        res = auth_client.get("/api/evaluations/eval_concurrent", headers=headers)
        expected_status = 404 if is_valid else 401
        return res.status_code, expected_status

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(_send_request, range(30)))

    for actual_status, expected_status in results:
        assert actual_status == expected_status
