"""Health endpoint."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    ai = AIService(settings=settings)
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        ai_provider=ai.provider_name,
        environment=settings.app_env,
    )
