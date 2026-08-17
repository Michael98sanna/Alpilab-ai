"""Minimal HTTP API surface (FastAPI).

Foundation phase: health check + AI ask endpoint using the mock provider.
No authentication, no paid APIs, no real AI providers.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ai.schemas import AIRequest
from app.core import get_settings
from app.schemas import AskRequest, AskResponse, HealthResponse
from app.services import AssistantService, build_router


def create_app(assistant: AssistantService | None = None) -> FastAPI:
    settings = get_settings()
    service = assistant or AssistantService(build_router(settings))

    api = FastAPI(
        title=settings.app_name,
        description=(
            "Alpilab AI — assistente tecnico cloud/web per laboratorio "
            "riparazione smartphone. Fondazione modulare; provider AI mock."
        ),
        version="0.1.0",
    )

    @api.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            app=settings.app_name,
            ai_provider=service.provider_name,
            ready=service.is_ready(),
        )

    @api.post("/v1/ask", response_model=AskResponse)
    def ask(body: AskRequest) -> AskResponse:
        if not body.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt vuoto")
        response = service.ask(
            body.prompt,
            kind=body.kind,
            image_paths=body.image_paths,
            metadata=body.metadata,
        )
        return AskResponse(
            content=response.content,
            provider=response.provider,
            model=response.model,
            metadata=response.metadata,
        )

    # Expose for tests without going through DI frameworks.
    api.state.assistant = service  # type: ignore[attr-defined]
    return api


# Module-level app for `uvicorn app.api:app`
app = create_app()
