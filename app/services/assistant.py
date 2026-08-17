"""Application services."""

from __future__ import annotations

from ai.router import AIRouter
from ai.schemas import AIGenerateRequest, AIGenerateResponse
from app.core.config import get_settings


class AssistantService:
    """Application-facing AI assistant service (provider-agnostic)."""

    def __init__(self, router: AIRouter | None = None) -> None:
        self._router = router or AIRouter()
        self._settings = get_settings()

    @property
    def active_provider(self) -> str:
        return self._router.provider_name

    def ask(self, prompt: str) -> AIGenerateResponse:
        request = AIGenerateRequest(prompt=prompt)
        return self._router.generate(request)
