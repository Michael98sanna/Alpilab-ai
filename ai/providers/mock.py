"""Offline mock provider — clearly identified as non-production.

Used to exercise the AI Router and application wiring without any
external API keys or network calls.
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIImageGenerateRequest,
)

from .base import AIProvider

MOCK_PREFIX = "[MOCK]"


class MockProvider(AIProvider):
    """Deterministic placeholder provider for local development and tests."""

    name = "mock"
    supports_images = True
    supports_streaming = True
    is_local = True
    is_cloud = False
    cost_tier = "free"

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        content = (
            f"{MOCK_PREFIX} Provider di test attivo.\n"
            f"Domanda ricevuta: {request.prompt}\n\n"
            "Questa risposta NON proviene da un modello AI reale. "
            "Il prossimo step sarà collegare provider locali o cloud "
            "che implementano la stessa interfaccia AIProvider."
        )
        return AIGenerateResponse(
            content=content,
            provider=self.name,
            model="mock-v0",
            is_mock=True,
            finish_reason="stop",
            metadata={"kind": request.hints.kind.value},
        )

    def generate_with_image(
        self, request: AIImageGenerateRequest
    ) -> AIGenerateResponse:
        image_ref = request.image_path or (
            "inline-b64" if request.image_bytes_b64 else "none"
        )
        content = (
            f"{MOCK_PREFIX} Analisi immagine simulata.\n"
            f"Prompt: {request.prompt}\n"
            f"Immagine: {image_ref}\n\n"
            "Nessuna computer vision reale è attiva in questa fase."
        )
        return AIGenerateResponse(
            content=content,
            provider=self.name,
            model="mock-vision-v0",
            is_mock=True,
            finish_reason="stop",
            metadata={"image_ref": image_ref},
        )

    def generate_stream(self, request: AIGenerateRequest) -> Iterator[str]:
        response = self.generate(request)
        # Yield in small chunks so streaming clients can be tested.
        chunk_size = 48
        text = response.content
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
