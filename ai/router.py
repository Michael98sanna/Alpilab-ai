"""AI Router: selects a provider without exposing vendor details to the app."""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIImageInput,
    ProviderCapability,
)


class AIRouter:
    """
    Routes requests to an available AI provider.

    Current behaviour (foundation phase):
    - Uses MockProvider by default
    - Allows injecting providers for tests
    - Exposes selection hooks for future local/cloud/cost/capability routing

    Complex routing (cost, fallback chains, per-request policy) is intentionally
    not implemented yet — only the extension points exist.
    """

    def __init__(
        self,
        providers: list[AIProvider] | None = None,
        default_provider: AIProvider | None = None,
    ) -> None:
        if default_provider is not None:
            self._providers: list[AIProvider] = [default_provider]
        elif providers:
            self._providers = list(providers)
        else:
            self._providers = [MockProvider()]

    @property
    def provider_name(self) -> str:
        return self.select_provider().name

    def list_providers(self) -> list[str]:
        return [p.name for p in self._providers]

    def select_provider(
        self,
        request: AIGenerateRequest | None = None,
    ) -> AIProvider:
        """
        Choose a provider for the given request.

        Future criteria (not yet active):
        - local vs cloud preference
        - fallback when unavailable
        - request kind / cost / capabilities
        - image requirement
        """
        available = [p for p in self._providers if p.is_available()]
        if not available:
            raise RuntimeError("Nessun provider AI disponibile.")

        if request is None:
            return available[0]

        # Minimal capability filter — ready for richer policy later.
        if request.require_image:
            vision = [
                p
                for p in available
                if p.supports(ProviderCapability.IMAGE)
            ]
            if vision:
                return vision[0]

        if request.prefer_local:
            local = [
                p
                for p in available
                if p.supports(ProviderCapability.LOCAL)
            ]
            if local:
                return local[0]

        return available[0]

    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        provider = self.select_provider(request)
        return provider.generate(request)

    def generate_with_image(
        self,
        request: AIGenerateRequest,
        image: AIImageInput,
    ) -> AIGenerateResponse:
        # Ensure image-capable selection when an image is supplied.
        enriched = request.model_copy(update={"require_image": True})
        provider = self.select_provider(enriched)
        return provider.generate_with_image(enriched, image)

    def generate_stream(self, request: AIGenerateRequest) -> Iterator[str]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Convenience helper used by the CLI entry point."""
        response = self.generate(AIGenerateRequest(prompt=prompt))
        return response.content
