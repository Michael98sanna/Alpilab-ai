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
        prompt = request.prompt.strip()
        lowered = prompt.lower()
        if lowered in {"ciao", "ciao!", "hello", "hi"}:
            content = "Ciao, sono Alpilab AI. Come posso aiutarti sulla riparazione?"
        else:
            content = (
                "[MOCK] Provider locale di test. "
                f"Ho ricevuto: {prompt}\n\n"
                "Nessun provider cloud è necessario. "
                "Il prossimo step è un modello locale opzionale (Ollama/llama.cpp)."
            )
        return AIResponse(
            content=content,
            provider=self.name,
            model="mock-v0",
            finish_reason="stop",
            metadata={"mock": True, "offline": True},
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
