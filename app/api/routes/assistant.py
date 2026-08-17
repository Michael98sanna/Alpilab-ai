"""Assistant HTTP endpoints. No vendor-specific payload leaks through."""

from fastapi import APIRouter, Depends

from app.api.deps import get_ai_router, get_assistant_service
from app.schemas.assistant import (
    AssistantAskRequest,
    AssistantAskResponse,
    ProviderInfo,
)
from app.services.assistant import AssistantService
from ai.router import AIRouter

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/providers", response_model=list[ProviderInfo])
def list_providers(ai_router: AIRouter = Depends(get_ai_router)) -> list[ProviderInfo]:
    infos: list[ProviderInfo] = []
    for provider in ai_router.providers:
        infos.append(
            ProviderInfo(
                name=provider.name,
                available=provider.is_available(),
                is_local=provider.capabilities.is_local,
                is_cloud=provider.capabilities.is_cloud,
                supports_images=provider.capabilities.supports_images,
                supports_streaming=provider.capabilities.supports_streaming,
                is_mock=provider.is_mock,
            )
        )
    return infos


@router.post("/ask", response_model=AssistantAskResponse)
def ask(
    payload: AssistantAskRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantAskResponse:
    response = service.ask(payload.question)
    return AssistantAskResponse.model_validate(response.model_dump())
