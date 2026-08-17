"""Common interface implemented by every AI provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ai.schemas import AIRequest, AIResponse, ProviderCapability


class AIProvider(ABC):
    """Provider-agnostic interface for text and multimodal generation.

    Application code must never depend on a concrete provider.
    Future local/cloud providers must implement this same contract.
    """

    name: str = "unknown"
    capabilities: frozenset[ProviderCapability] = frozenset(
        {ProviderCapability.TEXT}
    )

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the provider can serve requests right now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response for a text (or structured) request."""
        raise NotImplementedError

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        """Generate a response that may include image inputs.

        Default implementation rejects images unless the provider overrides it.
        """
        if not request.image_paths:
            return self.generate(request)
        raise NotImplementedError(
            f"Provider '{self.name}' does not support image generation yet."
        )

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        """Yield response chunks. Default: yield the full generate() result once."""
        response = self.generate(request)
        yield response.content

    def ask(self, prompt: str, **metadata: Any) -> str:
        """Convenience helper used by the CLI entry point."""
        response = self.generate(AIRequest(prompt=prompt, metadata=dict(metadata)))
        return response.content

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities
