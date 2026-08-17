"""Application services — orchestration without knowing provider details."""

from __future__ import annotations

from ai.router import AIRouter
from ai.schemas import AIGenerateRequest, AIGenerateResponse
from ai.prompts import SYSTEM_TECHNICAL_ASSISTANT
from app.core.config import get_settings


class AIService:
    """Application-facing AI service. Swappable providers via AIRouter."""

    def __init__(self, router: AIRouter | None = None) -> None:
        self._router = router or AIRouter()
        self._settings = get_settings()

    @property
    def provider_name(self) -> str:
        return self._router.provider_name

    def ask_technical(self, question: str) -> AIGenerateResponse:
        request = AIGenerateRequest(
            prompt=question,
            system_prompt=SYSTEM_TECHNICAL_ASSISTANT,
        )
        return self._router.generate(request)
