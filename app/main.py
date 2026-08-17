"""FastAPI application factory."""

from fastapi import FastAPI

from app import __version__
from app.api import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Alpilab AI — cloud-first technical assistant for smartphone repair labs. "
            "Foundation phase: MockProvider only, no real AI vendor lock-in."
        ),
    )
    application.include_router(api_router, prefix="/api")
    return application


app = create_app()
