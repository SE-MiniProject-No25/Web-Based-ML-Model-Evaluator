"""API Error Handler: turns AppError into the safe error format (Architecture section 10.4)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError


async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
    # Errors without an HTTP status only occur after the 202, inside the runner.
    return JSONResponse(status_code=exc.status_code or 500, content=exc.to_response_body())


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)
