"""Shared request/response schemas for the AI layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RequestKind(str, Enum):
    """High-level request categories used by the future router."""

    TEXT = "text"
    IMAGE = "image"
    DIAGNOSIS = "diagnosis"
    STREAM = "stream"


class ProviderCapability(str, Enum):
    """Capabilities a provider may declare."""

    TEXT = "text"
    IMAGE = "image"
    STREAM = "stream"
    LOCAL = "local"
    CLOUD = "cloud"


@dataclass(frozen=True)
class AIMessage:
    """Single message in a conversation."""

    role: str
    content: str


@dataclass
class AIRequest:
    """Normalized request passed to providers via the router."""

    prompt: str
    kind: RequestKind = RequestKind.TEXT
    messages: list[AIMessage] = field(default_factory=list)
    image_paths: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Future routing hints (not enforced yet)
    prefer_local: bool = False
    prefer_low_cost: bool = False
    require_capabilities: list[ProviderCapability] = field(default_factory=list)


@dataclass
class AIResponse:
    """Normalized response returned by providers."""

    content: str
    provider_name: str
    kind: RequestKind = RequestKind.TEXT
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_mock: bool = False
