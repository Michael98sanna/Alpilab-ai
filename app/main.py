"""FastAPI application factory."""

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description=(
            "Cloud-first technical AI assistant for smartphone repair labs. "
            "Separate from Alpilab Check. Provider-agnostic AI layer."
        ),
        version="0.1.0",
    )
    application.include_router(api_router, prefix="/api")
    return application


app = create_app()
