"""AI service — application-facing facade over the AI Router."""

from __future__ import annotations

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind
from app.core.config import Settings, get_settings


class AIService:
    """Keeps FastAPI / CLI callers free of provider details."""

    def __init__(
        self,
        router: AIRouter | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._router = router or AIRouter()

    @property
    def provider_name(self) -> str:
        return self._router.provider_name

    def ask(
        self,
        prompt: str,
        *,
        kind: RequestKind = RequestKind.GENERAL,
        image_paths: list[str] | None = None,
    ) -> AIResponse:
        request = AIRequest(
            prompt=prompt,
            kind=kind,
            image_paths=image_paths or [],
        )
        return self._router.generate(request)
