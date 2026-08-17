"""Abstract AI provider interface.

Every concrete provider (mock, local, OpenAI, Anthropic, Google, …)
must implement this contract so the application never depends on a
specific vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.schemas import (
        AIGenerateRequest,
        AIGenerateResponse,
        AIImageGenerateRequest,
    )


class AIProvider(ABC):
    """Provider-agnostic interface for text and image-aware generation."""

    name: str = "unknown"
    # Capability flags used by the router (future selection logic).
    supports_images: bool = False
    supports_streaming: bool = False
    is_local: bool = False
    is_cloud: bool = False
    cost_tier: str = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider can serve requests right now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: AIGenerateRequest) -> AIGenerateResponse:
        """Generate a complete text response."""
        raise NotImplementedError

    @abstractmethod
    def generate_with_image(
        self, request: AIImageGenerateRequest
    ) -> AIGenerateResponse:
        """Generate a response that may use an attached image.

        Providers without vision must raise NotImplementedError or return
        a clear unsupported response — never silently ignore the image.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_stream(
        self, request: AIGenerateRequest
    ) -> Iterator[str]:
        """Yield response tokens/chunks. Optional for early providers."""
        raise NotImplementedError

    def ask(self, prompt: str) -> str:
        """Convenience helper for simple text prompts (CLI / smoke tests)."""
        from ai.schemas import AIGenerateRequest

        return self.generate(AIGenerateRequest(prompt=prompt)).content
