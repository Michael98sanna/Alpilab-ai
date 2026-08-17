"""AI Router: selects a provider without exposing vendor details to the app.

Current phase: MockProvider only.
Future: local/cloud selection, fallback, cost/capability/image-aware routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .providers.base import AIProvider, GenerationRequest, GenerationResult
from .providers.mock import MockProvider
from .schemas import AIAskRequest, AIAskResponse, RoutePreference


@dataclass
class RouteDecision:
    """Explainable routing result (useful for logs and future UI)."""

    provider_name: str
    reason: str
    preference: RoutePreference


class AIRouter:
    """Selects the AI backend without exposing provider details to callers."""

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        fallback: AIProvider | None = None,
        default_provider_name: str = "mock",
    ) -> None:
        self._providers: dict[str, AIProvider] = {}
        primary = provider or MockProvider()
        self.register(primary)
        if fallback is not None:
            self.register(fallback)
        self._default_provider_name = default_provider_name
        if self._default_provider_name not in self._providers:
            self._default_provider_name = primary.name

    def register(self, provider: AIProvider) -> None:
        self._providers[provider.name] = provider

    @property
    def provider_name(self) -> str:
        return self._select_provider().name

    def available_providers(self) -> list[str]:
        return [
            name
            for name, provider in self._providers.items()
            if provider.is_available()
        ]

    def decide(
        self,
        *,
        preference: RoutePreference = RoutePreference.AUTO,
        has_images: bool = False,
        kind: str | None = None,
    ) -> RouteDecision:
        """Choose a provider. Complex strategies are intentionally not implemented yet."""
        # Future hooks (documented, not implemented):
        # - prefer local vs cloud from preference
        # - fallback when primary is unavailable
        # - select by cost / capability / request kind / image support
        _ = (has_images, kind)  # reserved for future routing signals

        provider = self._select_provider(preference=preference)
        reason = (
            f"Phase-1 routing: using '{provider.name}' "
            f"(preference={preference.value})."
        )
        return RouteDecision(
            provider_name=provider.name,
            reason=reason,
            preference=preference,
        )

    def generate(self, request: GenerationRequest) -> GenerationResult:
        decision = self.decide(
            has_images=bool(request.images),
        )
        provider = self._providers[decision.provider_name]
        if not provider.is_available():
            # Minimal fallback path for future multi-provider setups.
            for candidate in self._providers.values():
                if candidate.is_available():
                    provider = candidate
                    break
            else:
                raise RuntimeError("No AI provider is available.")
        return provider.generate(request)

    def ask(self, prompt: str) -> str:
        return self.generate(GenerationRequest(prompt=prompt)).text

    def ask_structured(self, payload: AIAskRequest) -> AIAskResponse:
        decision = self.decide(
            preference=payload.preference,
            has_images=payload.has_images,
            kind=payload.kind.value,
        )
        provider = self._providers[decision.provider_name]
        result = provider.generate(
            GenerationRequest(
                prompt=payload.prompt,
                metadata=dict(payload.metadata),
            )
        )
        return AIAskResponse(
            answer=result.text,
            provider=result.provider,
            model=result.model,
            routed_as=decision.reason,
        )

    def _select_provider(
        self,
        preference: RoutePreference = RoutePreference.AUTO,
    ) -> AIProvider:
        # Preference values are accepted now so callers can pass them, but
        # selection remains mock-first until real providers are registered.
        _ = preference
        provider = self._providers.get(self._default_provider_name)
        if provider is None:
            provider = next(iter(self._providers.values()))
        return provider


def build_default_router(settings: Any | None = None) -> AIRouter:
    """Factory used by API and CLI. Only MockProvider is registered for now."""
    provider_name = "mock"
    if settings is not None:
        provider_name = getattr(settings, "ai_provider", "mock") or "mock"

    # Real providers will be constructed here later based on settings.
    if provider_name != "mock":
        # Fail soft: keep the system runnable without external credentials.
        provider_name = "mock"

    return AIRouter(provider=MockProvider(), default_provider_name=provider_name)
