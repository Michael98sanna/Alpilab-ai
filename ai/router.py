"""AI Router — selects a provider without exposing vendor details to the app.

Future selection criteria (not implemented yet):
- local vs cloud
- fallback chains
- request kind / modality (text, image, diagnosis)
- cost / capability / availability
"""

from __future__ import annotations

from collections.abc import Iterator

from ai.providers.base import AIProvider
from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, AIResponse, RequestKind


class AIRouter:
    """Routes AI requests to an available provider.

    Current behaviour: always uses MockProvider (or an injected provider).
    Complex routing policies are intentionally deferred.
    """

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        fallback_providers: list[AIProvider] | None = None,
    ) -> None:
        self._provider = provider or MockProvider()
        # Reserved for future fallback chains — unused in this phase.
        self._fallback_providers = fallback_providers or []

    @property
    def provider_name(self) -> str:
        return self._provider.name

    def select_provider(self, request: AIRequest) -> AIProvider:
        """Choose a provider for the given request.

        Placeholder policy:
        - prefer the primary provider if available
        - otherwise try registered fallbacks
        - ignore cost/capability heuristics until real providers exist
        """
        if self._provider.is_available():
            return self._provider

        for candidate in self._fallback_providers:
            if candidate.is_available():
                return candidate

        # Last resort: return primary even if unavailable so callers get a clear error.
        return self._provider

    def generate(self, request: AIRequest) -> AIResponse:
        provider = self.select_provider(request)
        if request.image_paths or request.kind == RequestKind.IMAGE:
            return provider.generate_with_image(request)
        return provider.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str, *, kind: RequestKind = RequestKind.GENERAL) -> str:
        """Convenience wrapper for simple text prompts (CLI / early UI)."""
        response = self.generate(AIRequest(prompt=prompt, kind=kind))
        return response.content
