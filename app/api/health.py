"""Health endpoints."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
        "ai_provider": settings.ai_provider,
    }
