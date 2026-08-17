"""AI ask endpoint — uses MockProvider via the router."""

from fastapi import APIRouter

from app.schemas.ai import AskRequest, AskResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest) -> AskResponse:
    service = AIService()
    response = service.ask(
        body.prompt,
        kind=body.kind,
        image_paths=body.image_paths,
    )
    return AskResponse(
        content=response.content,
        provider=response.provider,
        kind=response.kind,
    )
