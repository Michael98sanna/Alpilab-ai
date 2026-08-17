"""Common interface implemented by every AI provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ai.schemas import AIRequest, AIResponse


class AIProvider(ABC):
    """Provider-agnostic interface for text and multimodal generation.

    Concrete providers (local, OpenAI, Google, Anthropic, …) must implement
    this contract so the rest of the application never depends on a vendor.
    """

    name: str = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when the provider can accept requests right now."""

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response for a text (or context-rich) request."""

    @abstractmethod
    def generate_with_image(self, request: AIRequest) -> AIResponse:
        """Generate a response that considers attached image paths.

        Implementations that do not support images should raise NotImplementedError
        or return a clear unavailable response — never silently ignore images.
        """

    @abstractmethod
    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        """Yield response chunks for streaming UIs."""

    # Backwards-compatible helper used by the CLI entrypoint.
    def ask(self, prompt: str) -> str:
        response = self.generate(AIRequest(prompt=prompt))
        return response.content
