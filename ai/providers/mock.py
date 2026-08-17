"""Offline mock provider used to exercise the architecture without external APIs.

This is intentionally a stub. It is clearly identified as MOCK and must not be
confused with a real AI backend.
"""

from __future__ import annotations

from typing import Iterator

from ai.providers.base import AIProvider
from ai.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
    ProviderCapability,
)


class MockProvider(AIProvider):
    """Deterministic offline provider for local development and tests."""

    name = "mock"
    capabilities = frozenset(
        {
            ProviderCapability.TEXT,
            ProviderCapability.IMAGE,
            ProviderCapability.STREAMING,
            ProviderCapability.LOCAL,
        }
    )

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        image_note = ""
        if request.has_images:
            image_note = (
                f" [MOCK] Immagini ricevute: {len(request.image_paths)} "
                "(analisi reale non ancora implementata)."
            )

        content = (
            "[MOCK PROVIDER] Nessun modello AI reale collegato.\n"
            f"Tipo richiesta: {request.kind.value}\n"
            f"Domanda ricevuta: {request.prompt}"
            f"{image_note}\n\n"
            "Il prossimo step sarà collegare provider locali e cloud "
            "tramite lo stesso contratto AIProvider."
        )
        return AIResponse(
            content=content,
            provider=self.name,
            model="mock-v1",
            metadata={"kind": request.kind.value, "mock": True},
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        if not request.has_images:
            raise ValueError("generate_with_image requires at least one image")
        return self.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[AIStreamChunk]:
        response = self.generate(request)
        # Simulate streaming by yielding two chunks.
        mid = max(1, len(response.content) // 2)
        yield AIStreamChunk(content=response.content[:mid], done=False)
        yield AIStreamChunk(content=response.content[mid:], done=True)
