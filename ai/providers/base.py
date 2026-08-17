"""Common interface implemented by every AI provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

from ai.schemas import AIRequest, AIResponse


@dataclass(frozen=True)
class ProviderCapabilities:
    """What a provider can do. Used later by the router for selection."""

    text: bool = True
    image: bool = False
    streaming: bool = False
    local: bool = False
    cloud: bool = False


class AIProvider(ABC):
    """Provider-agnostic interface for text and image generation.

    Concrete providers (local, OpenAI, Google, Anthropic, ...) must implement
    this class. The rest of the application must not import provider SDKs.
    """

    name: str = "unknown"
    capabilities: ProviderCapabilities = ProviderCapabilities()

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider can currently handle requests."""

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response for a text-oriented request."""

    @abstractmethod
    def generate_with_image(self, request: AIRequest) -> AIResponse:
        """Generate a response that may consider attached images."""

    @abstractmethod
    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        """Yield response chunks. Mock implementations may yield a single chunk."""
