"""AI Router — selects a provider without exposing vendor details.

Current behaviour (phase 1):
- Uses MockProvider by default
- Supports explicit provider injection for tests
- Records routing hints for future decision logic

Planned (not implemented yet):
- local vs cloud selection
- fallback chains
- selection by request kind / cost / capability / images / availability
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIImageGenerateRequest,
    RoutingHints,
)


class AIRouter:
    """Facade between application code and concrete AI providers."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        fallback_providers: list[AIProvider] | None = None,
    ) -> None:
        self._provider = provider or MockProvider()
        # Reserved for future fallback chains (unused in phase 1).
        self._fallback_providers = fallback_providers or []

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def provider(self) -> AIProvider:
        return self._provider

    def select_provider(self, hints: RoutingHints | None = None) -> AIProvider:
        """Choose a provider for the given hints.

        Phase 1: return the configured primary provider if available.
        Future: evaluate cost, capability, images, availability, fallback.
        """
        _ = hints  # reserved for future routing rules
        if self._provider.is_available():
            return self._provider

        for candidate in self._fallback_providers:
            if candidate.is_available():
                return candidate

        # Last resort: still return primary so callers get a clear mock/error.
        return self._provider

    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        provider = self.select_provider(request.hints)
        return provider.generate(request)

    def generate_with_image(
        self, request: AIImageGenerateRequest
    ) -> AIGenerateResponse:
        provider = self.select_provider(request.hints)
        return provider.generate_with_image(request)

    def generate_stream(self, request: AIGenerateRequest) -> Iterator[str]:
        provider = self.select_provider(request.hints)
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Simple text helper used by the CLI entry point."""
        return self.generate(AIGenerateRequest(prompt=prompt)).content
