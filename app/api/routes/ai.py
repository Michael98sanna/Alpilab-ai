"""AI HTTP endpoints. The route never imports a concrete provider SDK."""

from fastapi import APIRouter, Request

from app.schemas import GenerateRequest, GenerateResponse
from app.services.assistant import AssistantService

router = APIRouter()


@router.post("/ai/generate", response_model=GenerateResponse)
def generate(payload: GenerateRequest, request: Request) -> GenerateResponse:
    assistant: AssistantService = request.app.state.assistant
    response = assistant.ask(
        payload.prompt,
        images=payload.images,
        preferred_provider=payload.preferred_provider,
    )
    return GenerateResponse(
        text=response.text,
        provider_name=response.provider_name,
        is_mock=response.is_mock,
    )
