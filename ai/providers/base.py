"""Common interface implemented by every AI provider."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ai.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIImageInput,
    ProviderCapability,
)


class AIProvider(ABC):
    """
    Provider-agnostic interface for text and multimodal generation.

    The rest of the application must only depend on this contract,
    never on a concrete vendor SDK.
    """

    name: str = "unknown"
    capabilities: frozenset[ProviderCapability] = frozenset()

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider can serve requests right now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        """Generate a complete response for a text request."""
        raise NotImplementedError

    @abstractmethod
    def generate_with_image(
        self,
        request: AIGenerateRequest,
        image: AIImageInput,
    ) -> AIGenerateResponse:
        """Generate a response that considers an image input."""
        raise NotImplementedError

    @abstractmethod
    def generate_stream(self, request: AIGenerateRequest) -> Iterator[str]:
        """Yield response chunks. Providers without streaming may yield once."""
        raise NotImplementedError

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities
