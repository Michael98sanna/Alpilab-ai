"""Technical assistant service. Talks to the AI Router, never to a provider SDK."""

from __future__ import annotations

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, ImageInput, RequestKind


class AssistantService:
    def __init__(self, router: AIRouter | None = None) -> None:
        self._router = router or AIRouter()

    @property
    def provider_name(self) -> str:
        return self._router.provider_name

    def ask(
        self,
        prompt: str,
        *,
        images: list[ImageInput] | None = None,
        preferred_provider: str | None = None,
    ) -> AIResponse:
        kind = RequestKind.IMAGE if images else RequestKind.TEXT
        request = AIRequest(
            prompt=prompt,
            kind=kind,
            images=images or [],
            preferred_provider=preferred_provider,
        )
        return self._router.generate(request)
