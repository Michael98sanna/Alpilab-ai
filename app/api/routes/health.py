"""Health and readiness endpoints."""

from app.api.schemas import HealthResponse
from app.core.config import settings


def get_health() -> HealthResponse:
    """Return service health information for web/mobile clients."""
    return HealthResponse(ai_provider=settings.ai_provider)
