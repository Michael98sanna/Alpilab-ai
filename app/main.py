"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ai.router import AIRouter
from app import __version__
from app.api.routes import ai as ai_routes
from app.api.routes import health as health_routes
from app.core.config import Settings, get_settings
from app.services.assistant import AssistantService

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    application = FastAPI(
        title="Alpilab AI",
        version=__version__,
        description="Cloud-first technical assistant for a smartphone repair lab.",
    )
    application.state.settings = settings
    application.state.assistant = AssistantService(AIRouter())

    application.include_router(health_routes.router, prefix="/api")
    application.include_router(ai_routes.router, prefix="/api")

    if FRONTEND_DIR.is_dir():
        application.mount(
            "/",
            StaticFiles(directory=str(FRONTEND_DIR), html=True),
            name="frontend",
        )

    return application


app = create_app()
