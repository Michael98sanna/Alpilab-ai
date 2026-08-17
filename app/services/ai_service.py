"""AI service — application facade over the AI Router."""

from __future__ import annotations

from collections.abc import Iterator

from ai.router import AIRouter
from ai.schemas import AIRequest, AIResponse, RequestKind


class AIService:
    """Keeps application code independent from concrete AI providers."""

    def __init__(self, router: AIRouter | None = None) -> None:
        self._router = router or AIRouter()

    @property
    def provider_name(self) -> str:
        return self._router.provider_name

    def ask(self, prompt: str) -> str:
        return self._router.ask(prompt)

    def generate(self, prompt: str, *, kind: RequestKind = RequestKind.TEXT) -> AIResponse:
        return self._router.generate(AIRequest(prompt=prompt, kind=kind))

    def generate_with_images(
        self, prompt: str, image_paths: list[str]
    ) -> AIResponse:
        return self._router.generate(
            AIRequest(
                prompt=prompt,
                kind=RequestKind.IMAGE,
                image_paths=list(image_paths),
            )
        )

    def stream(self, prompt: str) -> Iterator[str]:
        return self._router.generate_stream(
            AIRequest(prompt=prompt, kind=RequestKind.STREAM)
        )
