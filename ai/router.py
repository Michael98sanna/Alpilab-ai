"""AI Router: selects a provider without exposing vendor details.

Phase 1 always uses MockProvider when available. The method signatures
already accept routing hints (local/cloud, cost, images, request type)
so a later policy can use them without changing callers.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from ai.exceptions import NoAvailableProviderError, ProviderNotSupportedError
from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import GenerationRequest, GenerationResponse, ImageGenerationRequest


@dataclass(frozen=True)
class RoutingHints:
    """Optional hints for future provider selection.

    Phase 1 only uses `requires_image` to skip providers that cannot
    accept image requests. Other fields are stored for later policies.
    """

    requires_image: bool = False
    prefer_local: bool = False
    prefer_low_cost: bool = False
    request_type: str | None = None


class AIRouter:
    """Facade used by the rest of the application."""

    def __init__(
        self,
        providers: Sequence[AIProvider] | None = None,
        default_name: str = "mock",
    ) -> None:
        registered = list(providers) if providers is not None else [MockProvider()]
        if not registered:
            raise NoAvailableProviderError("Nessun provider AI registrato.")
        self._providers: list[AIProvider] = registered
        self._default_name = default_name

    @property
    def providers(self) -> tuple[AIProvider, ...]:
        return tuple(self._providers)

    @property
    def provider_names(self) -> list[str]:
        return [provider.name for provider in self._providers]

    @property
    def provider_name(self) -> str:
        """Name of the default provider, for status endpoints and the CLI."""
        provider = self._default_provider()
        return provider.name if provider is not None else self._default_name

    def _default_provider(self) -> AIProvider | None:
        for provider in self._providers:
            if provider.name == self._default_name:
                return provider
        return self._providers[0] if self._providers else None

    def available_providers(self) -> list[AIProvider]:
        return [provider for provider in self._providers if provider.is_available()]

    def select_provider(self, hints: RoutingHints | None = None) -> AIProvider:
        """Choose a provider.

        Current policy:
        1. Keep only available providers.
        2. If images are required, keep only those that declare image support.
        3. Prefer the configured default name; otherwise the first remaining.

        Not implemented yet: cost, fallback chains, request-type maps.
        """
        hints = hints or RoutingHints()
        candidates = self.available_providers()
        if hints.requires_image:
            candidates = [
                provider
                for provider in candidates
                if provider.capabilities.supports_images
            ]
        if not candidates:
            raise NoAvailableProviderError(
                "Nessun provider AI disponibile per questa richiesta."
            )

        for provider in candidates:
            if provider.name == self._default_name:
                return provider
        return candidates[0]

    def generate(
        self,
        request: GenerationRequest,
        hints: RoutingHints | None = None,
    ) -> GenerationResponse:
        return self.select_provider(hints).generate(request)

    def generate_with_image(
        self,
        request: ImageGenerationRequest,
        hints: RoutingHints | None = None,
    ) -> GenerationResponse:
        effective = hints or RoutingHints()
        if not effective.requires_image:
            effective = RoutingHints(
                requires_image=True,
                prefer_local=effective.prefer_local,
                prefer_low_cost=effective.prefer_low_cost,
                request_type=effective.request_type,
            )
        return self.select_provider(effective).generate_with_image(request)

    def generate_stream(
        self,
        request: GenerationRequest,
        hints: RoutingHints | None = None,
    ) -> Iterator[str]:
        return self.select_provider(hints).generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Convenience wrapper used by the CLI."""
        response = self.generate(GenerationRequest(prompt=prompt))
        return response.text


def build_router(provider_name: str = "mock") -> AIRouter:
    """Factory used by the API. Only `mock` is implemented in this phase."""
    if provider_name != "mock":
        raise ProviderNotSupportedError(
            f"Provider '{provider_name}' non è implementato in questa fase. "
            "Usare AI_PROVIDER=mock."
        )
    return AIRouter(providers=[MockProvider()], default_name="mock")
