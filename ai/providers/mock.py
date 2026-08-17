"""Offline MockProvider used while real AI integrations are not connected.

This is intentionally a MOCK. It does not call external APIs.
"""

from __future__ import annotations

from collections.abc import Iterator

from .base import (
    AICapabilities,
    AIProvider,
    GenerationRequest,
    GenerationResult,
)


class MockProvider(AIProvider):
    """Deterministic offline provider for architecture and unit tests."""

    name = "mock"
    capabilities = AICapabilities(
        text=True,
        images=True,
        streaming=True,
        local=True,
        cloud=False,
    )

    def is_available(self) -> bool:
        return True

    def generate(self, request: GenerationRequest) -> GenerationResult:
        image_note = ""
        if request.images:
            image_note = f" [immagini ricevute: {len(request.images)}]"

        text = (
            "[MOCK PROVIDER] Nessun modello AI reale collegato.\n"
            f"Domanda: {request.prompt}{image_note}\n\n"
            "Questa risposta è un placeholder per verificare router, API e test."
        )
        return GenerationResult(
            text=text,
            provider=self.name,
            model="mock-v1",
            finish_reason="mock",
            metadata={"mock": True},
        )

    def generate_with_image(self, request: GenerationRequest) -> GenerationResult:
        if not request.images:
            raise ValueError("generate_with_image requires at least one image.")
        return self.generate(request)

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        result = self.generate(request)
        # Yield in two chunks so streaming paths can be tested without a real LLM.
        midpoint = max(1, len(result.text) // 2)
        yield result.text[:midpoint]
        yield result.text[midpoint:]
