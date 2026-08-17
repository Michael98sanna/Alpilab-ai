"""AI assistant API endpoints (mock-backed in this phase)."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.assistant import AssistantService

router = APIRouter(prefix="/ai", tags=["ai"])


class AskRequest(BaseModel):
    prompt: str = Field(min_length=1)


class AskResponse(BaseModel):
    content: str
    provider: str
    is_mock: bool


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    service = AssistantService()
    result = service.ask(body.prompt)
    return AskResponse(
        content=result.content,
        provider=result.provider,
        is_mock=result.is_mock,
    )
