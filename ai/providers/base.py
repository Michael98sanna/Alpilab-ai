"""Abstract AI provider contract.

Every current and future backend (local, OpenAI, Google, Anthropic, ...)
must implement this interface. Application code never talks to a vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass

from ai.schemas import GenerationRequest, GenerationResponse, ImageGenerationRequest


@dataclass(frozen=True)
class ProviderCapabilities:
    """What a provider can do. Used later by the router for selection."""

    supports_text: bool = True
    supports_images: bool = False
    supports_streaming: bool = False
    is_local: bool = False
    is_cloud: bool = False
    cost_tier: str = "unknown"


class AIProvider(ABC):
    """Vendor-agnostic text (and future multimodal) generation."""

    name: str = "unknown"
    is_mock: bool = False
    capabilities: ProviderCapabilities = ProviderCapabilities()

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider can serve a request right now."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Synchronous text generation."""

    @abstractmethod
    def generate_with_image(
        self, request: ImageGenerationRequest
    ) -> GenerationResponse:
        """Text generation that includes image references.

        Implementations that cannot handle images must raise a clear error.
        The mock accepts the call and states that it does not analyse pixels.
        """

    @abstractmethod
    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        """Yield response text chunks. May be a single chunk."""
