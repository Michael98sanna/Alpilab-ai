"""Provider that always fails — used in router fallback tests."""

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.schemas import AIRequest, AIResponse, ProviderCapability


class FailingProvider(AIProvider):
    """Simulates an unavailable or broken AI backend."""

    name = "failing"
    cost_per_call = 10

    def is_available(self) -> bool:
        return True

    def generate(self, request: AIRequest) -> AIResponse:
        raise RuntimeError("provider failed")

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        raise RuntimeError("provider failed")

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        raise RuntimeError("provider failed")
        yield ""  # pragma: no cover

    def capabilities(self) -> set[ProviderCapability]:
        return {ProviderCapability.TEXT_GENERATION, ProviderCapability.CLOUD}
