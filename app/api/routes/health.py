"""Liveness and phase metadata."""

from fastapi import APIRouter, Depends

from ai.router import AIRouter
from app.api.deps import get_ai_router
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(ai_router: AIRouter = Depends(get_ai_router)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="alpilab-ai",
        phase=settings.phase,
        provider=ai_router.provider_name,
        environment=settings.environment,
    )
