"""Application services — orchestration without provider lock-in."""

from __future__ import annotations

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind
from app.core import Settings, get_settings


def build_router(settings: Settings | None = None) -> AIRouter:
    """Build the AI router from settings.

    Foundation phase: only ``mock`` is supported. Other values raise clearly
    so we never silently pretend a real provider is connected.
    """
    settings = settings or get_settings()
    provider_name = settings.ai_provider.lower()

    if provider_name in {"mock", "test"}:
        return AIRouter()

    raise ValueError(
        f"Provider '{provider_name}' non ancora implementato. "
        "Usa AI_PROVIDER=mock in questa fase fondazionale."
    )


class AssistantService:
    """High-level assistant API used by CLI and HTTP layers."""

    def __init__(self, router: AIRouter | None = None) -> None:
        self._router = router or build_router()

    @property
    def provider_name(self) -> str:
        return self._router.provider_name

    def is_ready(self) -> bool:
        return self._router.is_ready()

    def ask(
        self,
        prompt: str,
        *,
        kind: RequestKind = RequestKind.GENERAL,
        image_paths: list[str] | None = None,
        metadata: dict | None = None,
    ) -> AIResponse:
        request = AIRequest(
            prompt=prompt,
            kind=kind,
            image_paths=tuple(image_paths or ()),
            metadata=dict(metadata or {}),
        )
        return self._router.generate(request)
