"""FastAPI application factory."""

from fastapi import FastAPI

from app.api import ai, health
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Assistente tecnico AI cloud-first per laboratorio riparazione smartphone. "
            "Progetto separato da Alpilab Check."
        ),
        version="0.1.0",
    )
    app.include_router(health.router)
    app.include_router(ai.router)
    return app


app = create_app()
