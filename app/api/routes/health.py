"""Health endpoint."""

from fastapi import APIRouter, Request

from app import __version__
from app.core.config import Settings
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service="alpilab-ai",
        version=__version__,
        ai_provider=settings.ai_provider,
        environment=settings.app_env,
    )
