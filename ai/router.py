"""Provider router for Alpilab AI."""

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, AIResponse, ProviderCapability


class AIRouter:
    """
    Selects an AI backend without exposing provider details to the application.

    Future routing dimensions (not yet implemented):
    - local vs cloud providers
    - fallback when a provider is unavailable
    - request type (text vs image)
    - cost, capability, and availability
    """

    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        self._providers: list[AIProvider] = providers or [MockProvider()]
        self._default_provider = self._providers[0]

    @property
    def provider_name(self) -> str:
        return self._default_provider.name

    def list_providers(self) -> list[str]:
        return [provider.name for provider in self._providers]

    def select_provider(self, request: AIRequest) -> AIProvider:
        """Pick the best available provider for a request (simple logic for now)."""
        if request.images:
            for provider in self._providers:
                if (
                    provider.is_available()
                    and ProviderCapability.IMAGE_INPUT in provider.capabilities()
                ):
                    return provider

        for provider in self._providers:
            if provider.is_available():
                return provider

        return self._default_provider

    def generate(self, request: AIRequest) -> AIResponse:
        provider = self.select_provider(request)
        if request.images:
            return provider.generate_with_image(request)
        return provider.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Convenience helper for simple text prompts."""
        response = self.generate(AIRequest(prompt=prompt))
        return response.content
