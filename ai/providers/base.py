"""Common interface implemented by every AI provider.

Real cloud/local providers will implement this contract. Application code must
never depend on a specific vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AICapabilities:
    """What a provider can do; used later by the AI Router for selection."""

    text: bool = True
    images: bool = False
    streaming: bool = False
    local: bool = False
    cloud: bool = False


@dataclass
class GenerationRequest:
    """Normalized request passed to any AIProvider."""

    prompt: str
    system_prompt: str | None = None
    images: list[bytes] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Normalized provider response."""

    text: str
    provider: str
    model: str | None = None
    finish_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Provider-agnostic interface for text and multimodal generation."""

    name: str = "unknown"
    capabilities: AICapabilities = AICapabilities()

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider can accept requests right now."""
        raise NotImplementedError

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate a complete text response."""
        raise NotImplementedError

    def generate_with_image(self, request: GenerationRequest) -> GenerationResult:
        """Generate a response that may include image inputs.

        Default implementation rejects when the provider lacks image support.
        """
        if not self.capabilities.images:
            raise NotImplementedError(
                f"Provider '{self.name}' does not support image inputs."
            )
        if not request.images:
            raise ValueError("generate_with_image requires at least one image.")
        return self.generate(request)

    def generate_stream(self, request: GenerationRequest) -> Iterator[str]:
        """Stream response chunks. Default: yield the full generate() result."""
        if not self.capabilities.streaming:
            result = self.generate(request)
            yield result.text
            return
        raise NotImplementedError(
            f"Provider '{self.name}' advertises streaming but does not implement it."
        )

    def ask(self, prompt: str) -> str:
        """Convenience wrapper used by the CLI and simple callers."""
        return self.generate(GenerationRequest(prompt=prompt)).text
