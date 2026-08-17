"""AI endpoints (mock provider only in this phase)."""

from fastapi import APIRouter

from ai.schemas import AIAskRequest, AIAskResponse
from app.services.ai_service import AIService

router = APIRouter()
_service = AIService()


@router.post("/ask", response_model=AIAskResponse)
def ask(payload: AIAskRequest) -> AIAskResponse:
    """Ask the technical assistant (routed through AIRouter → MockProvider)."""
    return _service.ask_structured(payload)


@router.get("/providers")
def list_providers() -> dict:
    return {
        "available": _service.router.available_providers(),
        "active": _service.router.provider_name,
        "note": "Only MockProvider is registered in this foundation phase.",
    }
