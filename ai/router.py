"""AI Router — selects which provider handles a request.

Current behaviour (foundation phase):
- Uses MockProvider by default.
- Accepts an injected provider for tests.

Future responsibilities (NOT implemented yet):
- choose local vs cloud providers
- fallback chains
- routing by request kind / cost / capability / images / availability
"""

from __future__ import annotations

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import (
    AIRequest,
    AIResponse,
    AIStreamChunk,
    ProviderCapability,
    RequestKind,
)
from typing import Iterator


class AIRouter:
    """Routes AI requests to an available provider without leaking provider details."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        fallback_providers: list[AIProvider] | None = None,
    ) -> None:
        self._provider = provider or MockProvider()
        # Reserved for future fallback chains; unused in this phase.
        self._fallback_providers = list(fallback_providers or [])

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def provider(self) -> AIProvider:
        return self._provider

    def is_ready(self) -> bool:
        return self._provider.is_available()

    def select_provider(self, request: AIRequest) -> AIProvider:
        """Choose a provider for the request.

        Foundation phase: return the configured provider if available.
        Future: inspect kind, images, cost, capabilities, availability.
        """
        # Placeholders for future routing signals (intentionally unused).
        _ = (
            request.kind,
            request.has_images,
            ProviderCapability.IMAGE,
            RequestKind.IMAGE_ANALYSIS,
        )

        if self._provider.is_available():
            return self._provider

        for candidate in self._fallback_providers:
            if candidate.is_available():
                return candidate

        raise RuntimeError(
            f"Nessun provider AI disponibile (primario: {self._provider.name})."
        )

    def generate(self, request: AIRequest) -> AIResponse:
        provider = self.select_provider(request)
        if request.has_images:
            return provider.generate_with_image(request)
        return provider.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[AIStreamChunk]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str, *, kind: RequestKind = RequestKind.GENERAL) -> str:
        """Convenience API used by the CLI entry point."""
        response = self.generate(AIRequest(prompt=prompt, kind=kind))
        return response.content
