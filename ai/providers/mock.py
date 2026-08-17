"""Offline MockProvider — clearly a test stub, not a real AI backend."""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.schemas import AIRequest, AIResponse, RequestKind


class MockProvider(AIProvider):
    """Deterministic provider used to exercise the architecture without APIs.

    MOCK: does not call any external model. Safe for local tests and demos.
    """

    name = "mock"

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        content = (
            "[MOCK PROVIDER] Risposta di test.\n"
            f"Domanda ricevuta: {request.prompt}\n"
            f"Tipo richiesta: {request.kind.value}\n"
            "Nessun modello reale è collegato. "
            "Il prossimo step sarà registrare provider locali/cloud dietro questa stessa interfaccia."
        )
        return AIResponse(
            content=content,
            provider=self.name,
            kind=request.kind,
            confidence=None,
            metadata={"mock": True},
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        images = request.image_paths or ["<nessuna>"]
        content = (
            "[MOCK PROVIDER] Analisi immagini simulata.\n"
            f"Domanda: {request.prompt}\n"
            f"Immagini: {', '.join(images)}\n"
            "Questa è una risposta stub: nessuna computer vision è attiva."
        )
        return AIResponse(
            content=content,
            provider=self.name,
            kind=RequestKind.IMAGE,
            confidence=None,
            metadata={"mock": True, "image_count": len(request.image_paths)},
        )

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        response = self.generate(request)
        # Yield the mock answer in small chunks so streaming clients can be tested.
        chunk_size = 40
        text = response.content
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
