"""Application entry point: ``uvicorn app.main:app`` (see the README)."""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.config import Settings, load_settings
from app.storage import TemporaryStorage


def create_app(settings: Settings = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Web-Based ML Model Evaluator")
    app.state.settings = settings
    app.state.storage = TemporaryStorage(settings.storage_dir)
    register_error_handlers(app)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
