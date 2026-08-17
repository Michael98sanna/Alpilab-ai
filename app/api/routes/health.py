"""Health / readiness endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "ai_provider": settings.ai_provider,
    }
