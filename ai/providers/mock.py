"""Offline provider used while real AI integrations are being built."""

from collections.abc import Iterator

from ai.schemas import AIRequest, AIResponse, ProviderCapability

from .base import AIProvider


class MockProvider(AIProvider):
    """Mock provider for architecture validation without external services."""

    name = "mock"

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            content=(
                "[MOCK] Provider di test attivo. "
                f"Prompt ricevuto: {request.prompt}\n\n"
                "Il prossimo step sarà collegare un vero modello AI."
            ),
            provider=self.name,
            model="mock-v0",
            finish_reason="stop",
            metadata={"mock": True},
        )

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        image_count = len(request.images)
        base = self.generate(request)
        base.content = (
            f"{base.content}\n\n"
            f"[MOCK] Immagini ricevute: {image_count}."
        )
        return base

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        response = self.generate(request)
        words = response.content.split(" ")
        for index, word in enumerate(words):
            yield word if index == 0 else f" {word}"

    def capabilities(self) -> set[ProviderCapability]:
        return {
            ProviderCapability.TEXT_GENERATION,
            ProviderCapability.IMAGE_INPUT,
            ProviderCapability.STREAMING,
            ProviderCapability.LOCAL,
        }
