"""Offline mock provider used while real AI integrations are not wired."""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIImageInput,
    ProviderCapability,
)


class MockProvider(AIProvider):
    """
    Clearly identified mock provider for architecture and tests.

    Does not call any external API. Safe for local development.
    """

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

    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        content = (
            "[MOCK PROVIDER] Risposta di test.\n"
            f"Domanda ricevuta: {request.prompt}\n\n"
            "Nessun modello AI reale è collegato. "
            "Sostituisci questo provider tramite AI Router quando disponibile."
        )
        return AIGenerateResponse(
            content=content,
            provider=self.name,
            model="mock-v1",
            is_mock=True,
            metadata={"kind": request.kind.value},
        )

    def generate_with_image(
        self,
        request: AIGenerateRequest,
        image: AIImageInput,
    ) -> AIGenerateResponse:
        image_hint = image.description or image.path or "(nessuna descrizione)"
        content = (
            "[MOCK PROVIDER] Analisi immagine di test.\n"
            f"Domanda: {request.prompt}\n"
            f"Immagine: {image_hint}\n\n"
            "Nessuna computer vision reale è attiva in questa fase."
        )
        return AIGenerateResponse(
            content=content,
            provider=self.name,
            model="mock-v1-vision",
            is_mock=True,
            metadata={"kind": request.kind.value, "has_image": True},
        )

    def generate_stream(self, request: AIGenerateRequest) -> Iterator[str]:
        response = self.generate(request)
        # Simple chunking so streaming callers can be exercised without a real LLM.
        chunk_size = 48
        text = response.content
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
