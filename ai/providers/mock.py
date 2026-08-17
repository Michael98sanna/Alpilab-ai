"""Offline mock provider for architecture and unit tests.

This is intentionally a MOCK — it does not call any real AI service.
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.schemas import (
    AIRequest,
    AIResponse,
    ProviderCapability,
    RequestKind,
)


class MockProvider(AIProvider):
    """Deterministic offline provider used while real integrations are pending."""

    name = "mock"
    capabilities = frozenset(
        {
            ProviderCapability.TEXT,
            ProviderCapability.IMAGE,
            ProviderCapability.STREAM,
            ProviderCapability.LOCAL,
        }
    )

    def __init__(self, *, available: bool = True) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def generate(self, request: AIRequest) -> AIResponse:
        content = (
            "[MOCK] Provider di test attivo.\n"
            f"Domanda ricevuta: {request.prompt}\n\n"
            "Questa risposta è generata localmente senza chiamate esterne. "
            "Il prossimo passo sarà collegare provider AI reali dietro la stessa interfaccia."
        )
        return AIResponse(
            content=content,
            provider_name=self.name,
            kind=request.kind,
            confidence=0.0,
            metadata={"mock": True, "request_kind": request.kind.value},
            is_mock=True,
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        image_note = (
            f"Immagini allegate (mock): {len(request.image_paths)}"
            if request.image_paths
            else "Nessuna immagine allegata."
        )
        base = self.generate(
            AIRequest(
                prompt=request.prompt,
                kind=RequestKind.IMAGE,
                messages=request.messages,
                image_paths=request.image_paths,
                metadata=request.metadata,
            )
        )
        return AIResponse(
            content=f"{base.content}\n{image_note}",
            provider_name=self.name,
            kind=RequestKind.IMAGE,
            confidence=0.0,
            metadata={**base.metadata, "image_count": len(request.image_paths)},
            is_mock=True,
        )

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        response = self.generate(request)
        # Yield in small chunks so streaming plumbing can be tested.
        chunk_size = 48
        text = response.content
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
