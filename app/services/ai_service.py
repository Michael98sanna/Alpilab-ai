"""Thin service wrapping the AI Router for API / CLI callers."""

from __future__ import annotations

from ai.router import AIRouter, build_default_router
from ai.schemas import AIAskRequest, AIAskResponse
from app.core.config import Settings, get_settings


class AIService:
    """Application-facing AI operations."""

    def __init__(
        self,
        router: AIRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.router = router or build_default_router(self.settings)

    def ask(self, prompt: str) -> str:
        return self.router.ask(prompt)

    def ask_structured(self, payload: AIAskRequest) -> AIAskResponse:
        return self.router.ask_structured(payload)
