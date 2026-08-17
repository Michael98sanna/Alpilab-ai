"""AI-related API endpoints (provider-agnostic)."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ai_service import AIService

router = APIRouter()
_service = AIService()


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    provider: str
    is_mock: bool


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    result = _service.ask_technical(body.question)
    return AskResponse(
        answer=result.content,
        provider=result.provider,
        is_mock=result.is_mock,
    )


@router.get("/provider")
def provider_info() -> dict:
    return {
        "provider": _service.provider_name,
        "note": "Phase 1 uses MockProvider only. Real providers come later.",
    }
