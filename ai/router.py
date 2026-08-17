"""AI Router: selects a provider without exposing it to the rest of the app.

Current behaviour is intentionally simple: use the first available registered
provider (MockProvider by default).

Future selection may consider:
- local vs cloud
- fallback chains
- request kind
- cost
- capabilities (text, image, streaming)
- presence of images
- availability
Those policies are not implemented yet.
"""

from __future__ import annotations

from collections.abc import Iterator

from .providers.base import AIProvider
from .providers.mock import MockProvider
from .schemas import AIRequest, AIResponse, RequestKind


class NoProviderAvailable(Exception):
    """Raised when no registered provider reports itself as available."""


class AIRouter:
    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        self._providers: list[AIProvider] = list(providers) if providers else [MockProvider()]

    @property
    def provider_name(self) -> str:
        return self.select_provider(AIRequest(prompt="")).name

    def register(self, provider: AIProvider) -> None:
        self._providers.append(provider)

    def available_providers(self) -> list[AIProvider]:
        return [provider for provider in self._providers if provider.is_available()]

    def select_provider(self, request: AIRequest) -> AIProvider:
        available = self.available_providers()
        if not available:
            raise NoProviderAvailable("No AI provider is currently available.")

        if request.preferred_provider:
            for provider in available:
                if provider.name == request.preferred_provider:
                    return provider

        return available[0]

    def generate(self, request: AIRequest) -> AIResponse:
        provider = self.select_provider(request)
        if request.has_images:
            return provider.generate_with_image(request)
        return provider.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Convenience wrapper used by the CLI and simple callers."""

        response = self.generate(AIRequest(prompt=prompt, kind=RequestKind.TEXT))
        return response.text
