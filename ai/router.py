"""Provider router for Alpilab AI."""

from collections.abc import Iterator
import os

from ai.providers.base import AIProvider
from ai.providers.local import LocalAIProvider
from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, AIResponse, ProviderCapability


class AIRouter:
    """
    Selects an AI backend without exposing provider details to the application.

    Local and cloud providers are optional. MockProvider always works offline.
    """

    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        self._providers: list[AIProvider] = providers or self._default_providers()
        self._default_provider = self._providers[0]

    @staticmethod
    def _default_providers() -> list[AIProvider]:
        local_url = os.getenv("ALPILAB_LOCAL_AI_URL", "").strip() or None
        return [MockProvider(), LocalAIProvider(local_url)]

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
            if (
                provider.name == "local"
                and provider.is_available()
                and ProviderCapability.LOCAL in provider.capabilities()
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
