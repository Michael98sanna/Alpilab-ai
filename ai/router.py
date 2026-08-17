"""AI Router — selects a provider without exposing it to application code.

Future extensions (not implemented yet):
- local vs cloud preference
- fallback chains
- cost / capability / availability based selection
- image-aware routing
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, AIResponse, RequestKind


class AIRouter:
    """Routes AI requests to an available provider.

    Current behaviour: use the injected provider, or fall back to MockProvider.
    Selection logic is deliberately minimal and documented for future growth.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        providers: list[AIProvider] | None = None,
    ) -> None:
        registered = list(providers or [])
        if provider is not None:
            registered.insert(0, provider)
        if not registered:
            registered.append(MockProvider())
        self._providers = registered
        self._provider = self._select_provider()

    def _select_provider(self) -> AIProvider:
        """Choose the first available provider.

        Placeholder for future policies (cost, capability, locality, fallback).
        """
        for candidate in self._providers:
            if candidate.is_available():
                return candidate
        # Last resort: first registered provider even if unavailable (tests can assert).
        return self._providers[0]

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def active_provider(self) -> AIProvider:
        return self._provider

    def list_providers(self) -> list[str]:
        return [p.name for p in self._providers]

    def generate(self, request: AIRequest) -> AIResponse:
        provider = self._select_provider()
        self._provider = provider
        if request.kind == RequestKind.IMAGE or request.image_paths:
            return provider.generate_with_image(request)
        return provider.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        provider = self._select_provider()
        self._provider = provider
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """CLI / simple-text convenience wrapper."""
        response = self.generate(AIRequest(prompt=prompt, kind=RequestKind.TEXT))
        return response.content
