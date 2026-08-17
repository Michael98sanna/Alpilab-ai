"""Shared request/response schemas for the AI layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator


class RequestKind(str, Enum):
    """High-level request categories used by the router (future routing rules)."""

    GENERAL = "general"
    DIAGNOSIS = "diagnosis"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENTATION = "documentation"
    GUIDED_STEPS = "guided_steps"


class ProviderCapability(str, Enum):
    """Capabilities a provider may advertise."""

    TEXT = "text"
    IMAGE = "image"
    STREAMING = "streaming"
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass(frozen=True)
class AIRequest:
    """Normalized request passed to providers via the router."""

    prompt: str
    kind: RequestKind = RequestKind.GENERAL
    image_paths: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_images(self) -> bool:
        return bool(self.image_paths)


@dataclass(frozen=True)
class AIResponse:
    """Normalized provider response."""

    content: str
    provider: str
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIStreamChunk:
    """Single chunk from a streaming generation."""

    content: str
    done: bool = False


StreamIterator = Iterator[AIStreamChunk]
