"""Authentication Middleware and credential verification (Architecture sections 3, 5, 10, 11).

Enforces optional API-key authentication on evaluation and result endpoints (SEC-06, NFR-07).
Authentication is disabled by default; when enabled, protected endpoints require either an
``X-API-Key: <key>`` header or an ``Authorization: Bearer <key>`` header.
"""

import logging
import posixpath
import secrets
from urllib.parse import unquote

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import Settings, load_settings
from app.errors import HTTP_STATUS, AppError, ErrorCode

logger = logging.getLogger(__name__)


def is_protected_path(path: str) -> bool:
    """Check whether a request URL path targets protected evaluation endpoints.

    All /api/evaluations* routes are protected. Non-evaluation routes like
    /api/health remain unauthenticated.

    Normalizes URL percent-encoding, multi-slash sequences, backslashes, and
    dot-dot path traversals to ensure robust access control.
    """
    unquoted = unquote(path).replace("\\", "/")
    norm = posixpath.normpath(unquoted)
    normalized = "/" + norm.lstrip("/")
    normalized = normalized.rstrip("/")
    return normalized == "/api/evaluations" or normalized.startswith("/api/evaluations/")


def extract_credentials(request: Request) -> list[str]:
    """Extract candidate API keys from supported headers.

    Supports:
    - X-API-Key: <key>
    - Authorization: Bearer <key>

    Handles single and duplicate headers gracefully.
    Never logs or exposes the extracted credentials.
    """
    candidates: list[str] = []

    # 1. Check X-API-Key headers (handles duplicate and comma-separated headers)
    for x_api_key in request.headers.getlist("x-api-key"):
        for part in x_api_key.split(","):
            cleaned = part.strip()
            if cleaned:
                candidates.append(cleaned)

    # 2. Check Authorization headers for Bearer scheme (handles duplicate headers)
    for auth_header in request.headers.getlist("authorization"):
        parts = auth_header.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            cleaned = parts[1].strip()
            if cleaned:
                candidates.append(cleaned)

    return candidates


def verify_api_key(request: Request, configured_key: str | None) -> bool:
    """Verify incoming request credentials against the configured API key.

    Uses secrets.compare_digest() with UTF-8 byte encoding for constant-time comparison.
    Handles non-ASCII characters safely without raising TypeError.
    Fails securely (returns False) if no key or an empty key is configured.
    """
    if not configured_key or not configured_key.strip():
        # Fail-secure: authentication is enabled, but no valid key is configured.
        return False

    candidates = extract_credentials(request)
    if not candidates:
        return False

    configured_bytes = configured_key.strip().encode("utf-8")
    authenticated = False
    for candidate in candidates:
        try:
            cand_bytes = candidate.encode("utf-8")
            if secrets.compare_digest(cand_bytes, configured_bytes):
                authenticated = True

            # If ASGI/Starlette decoded wire bytes as latin-1, recover the original wire bytes.
            try:
                raw_wire_bytes = candidate.encode("latin-1")
                if secrets.compare_digest(raw_wire_bytes, configured_bytes):
                    authenticated = True
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        except Exception:
            # Safely disregard candidate on any encoding error
            continue

    return authenticated


def unauthenticated_response() -> JSONResponse:
    """Return the standard 401 UNAUTHENTICATED error envelope."""
    err = AppError(ErrorCode.UNAUTHENTICATED, "Authentication required.")
    return JSONResponse(
        status_code=HTTP_STATUS[err.code],
        content=err.to_response_body(),
    )


class AuthenticationMiddleware:
    """ASGI middleware enforcing optional authentication on protected endpoints."""

    def __init__(self, app: ASGIApp, settings: Settings | None = None) -> None:
        self.app = app
        self._settings = settings

    def _resolve_settings(self, request: Request) -> Settings:
        if self._settings is not None:
            return self._settings
        app = request.scope.get("app")
        if app is not None and hasattr(app, "state"):
            settings = getattr(app.state, "settings", None)
            if settings is not None:
                return settings
        return load_settings()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        settings = self._resolve_settings(request)

        if settings.auth_enabled and is_protected_path(request.url.path):
            if not verify_api_key(request, settings.api_key):
                logger.warning(
                    "Unauthenticated request to %s (method: %s)",
                    request.url.path,
                    request.method,
                )
                response = unauthenticated_response()
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
