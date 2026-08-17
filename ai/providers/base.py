"""Common interface implemented by every AI provider.

All providers (local, cloud, mock) must implement this contract so the rest
of the application never depends on a specific backend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from ai.schemas import AIRequest, AIResponse, AIStreamChunk, ProviderCapability


class AIProvider(ABC):
    """Provider-agnostic interface for text and image-aware generation."""

    name: str = "unknown"
    capabilities: frozenset[ProviderCapability] = frozenset(
        {ProviderCapability.TEXT}
    )

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider can serve requests right now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response for a text (or multimodal) request."""
        raise NotImplementedError

    def generate_with_image(self, request: AIRequest) -> AIResponse:
        """Generate a response that may include image context.

        Default implementation delegates to ``generate``. Providers that
        support vision should override this method.
        """
        if not request.has_images:
            raise ValueError("generate_with_image requires at least one image")
        return self.generate(request)

    def generate_stream(self, request: AIRequest) -> Iterator[AIStreamChunk]:
        """Stream response chunks. Default: yield the full response once."""
        response = self.generate(request)
        yield AIStreamChunk(content=response.content, done=True)

    def ask(self, prompt: str) -> str:
        """Convenience wrapper for simple text prompts (CLI / early callers)."""
        response = self.generate(AIRequest(prompt=prompt))
        return response.content
