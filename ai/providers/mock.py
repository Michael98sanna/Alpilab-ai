"""Offline mock provider.

This is a test double, not a real model. It echoes the prompt and never
calls an external API. Responses are clearly marked as MOCK.
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.schemas import GenerationRequest, GenerationResponse, ImageGenerationRequest

from .base import AIProvider, ProviderCapabilities

_MOCK_PREFIX = "[MOCK]"


class MockProvider(AIProvider):
    """Always-available local stub used to exercise routing and the API."""

    name = "mock"
    is_mock = True
    capabilities = ProviderCapabilities(
        supports_text=True,
        supports_images=True,
        supports_streaming=True,
        is_local=True,
        is_cloud=False,
        cost_tier="free",
    )

    def is_available(self) -> bool:
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        text = (
            f"{_MOCK_PREFIX} Provider di test. Nessun modello AI è collegato.\n"
            f"Domanda ricevuta: {request.prompt}\n\n"
            "Questa risposta non è una diagnosi. Il passo successivo è "
            "collegare un vero provider tramite l'interfaccia AIProvider."
        )
        return GenerationResponse(
            text=text,
            provider_name=self.name,
            is_mock=True,
            facts=[],
            detected_data=[],
            hypotheses=[],
            recommended_checks=[
                "Verificare i sintomi al banco prima di ogni conclusione.",
            ],
            confidence=None,
        )

    def generate_with_image(
        self, request: ImageGenerationRequest
    ) -> GenerationResponse:
        names = ", ".join(image.filename for image in request.images)
        text = (
            f"{_MOCK_PREFIX} Richiesta con immagini accettata, ma questo "
            "provider NON analizza i pixel.\n"
            f"File riferiti: {names}\n"
            f"Prompt: {request.prompt}"
        )
        return GenerationResponse(
            text=text,
            provider_name=self.name,
            is_mock=True,
            facts=[],
            detected_data=[f"riferimenti_immagine={len(request.images)}"],
            hypotheses=[],
            recommended_checks=[],
            confidence=None,
        )

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        response = self.generate(request)
        yield response.text
