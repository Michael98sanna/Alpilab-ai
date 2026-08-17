"""Common interface implemented by every AI provider."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ai.schemas import AIRequest, AIResponse, ProviderCapability


class AIProvider(ABC):
    """Provider-agnostic interface for AI generation."""

    name: str = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether this provider can accept requests right now."""

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response for the given request."""

    @abstractmethod
    def generate_with_image(self, request: AIRequest) -> AIResponse:
        """Generate a response that includes image input."""

    @abstractmethod
    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        """Stream partial response chunks for the given request."""

    def capabilities(self) -> set[ProviderCapability]:
        """Return the capabilities advertised by this provider."""
        return {ProviderCapability.TEXT_GENERATION}
