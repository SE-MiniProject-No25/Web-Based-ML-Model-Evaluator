"""Application entry point: ``uvicorn app.main:app`` (see the README)."""

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.evaluations import router as evaluations_router
from app.config import Settings, load_settings
from app.results import ResultService
from app.storage import TemporaryStorage


def create_app(settings: Settings | None = None, results: ResultService | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Web-Based ML Model Evaluator")
    app.state.settings = settings
    app.state.storage = TemporaryStorage(settings.storage_dir)
    app.state.results = results or ResultService()
    register_error_handlers(app)
    app.include_router(evaluations_router)

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
