"""Offline mock provider. Clearly identified as a test double, not a real model."""

from __future__ import annotations

from collections.abc import Iterator

from ai.schemas import AIRequest, AIResponse, RequestKind

from .base import AIProvider, ProviderCapabilities

MOCK_BANNER = "[MOCK PROVIDER]"


class MockProvider(AIProvider):
    """Deterministic provider used until real local/cloud backends exist."""

    name = "mock"
    capabilities = ProviderCapabilities(
        text=True,
        image=True,
        streaming=True,
        local=True,
        cloud=False,
    )

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        text = self._compose(request)
        return AIResponse(
            text=text,
            provider_name=self.name,
            is_mock=True,
            request_kind=request.kind,
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        if not request.has_images:
            raise ValueError("generate_with_image requires at least one image.")
        names = ", ".join(image.filename for image in request.images)
        extra = f" Immagini allegate (non analizzate): {names}."
        return AIResponse(
            text=self._compose(request) + extra,
            provider_name=self.name,
            is_mock=True,
            request_kind=RequestKind.IMAGE,
        )

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        yield self._compose(request)

    def _compose(self, request: AIRequest) -> str:
        return (
            f"{MOCK_BANNER} Nessun modello reale e' collegato. "
            f"Domanda ricevuta: {request.prompt}"
        )
