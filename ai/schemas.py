"""Shared request/response schemas for the AI layer."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RequestKind(str, Enum):
    """High-level request categories used by the router (future routing)."""

    TEXT = "text"
    IMAGE = "image"
    DIAGNOSIS = "diagnosis"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class ProviderCapability(str, Enum):
    """Capabilities a provider may advertise."""

    TEXT = "text"
    IMAGE = "image"
    STREAMING = "streaming"
    LOCAL = "local"
    CLOUD = "cloud"


class AIMessage(BaseModel):
    """Single chat message."""

    role: str = Field(description="Message role: system | user | assistant")
    content: str


class AIGenerateRequest(BaseModel):
    """Normalized generation request independent of provider."""

    prompt: str
    messages: list[AIMessage] = Field(default_factory=list)
    kind: RequestKind = RequestKind.GENERAL
    prefer_local: bool = False
    prefer_low_cost: bool = False
    require_image: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIGenerateResponse(BaseModel):
    """Normalized generation response independent of provider."""

    content: str
    provider: str
    model: str | None = None
    is_mock: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIImageInput(BaseModel):
    """Image payload for multimodal generation (placeholder-friendly)."""

    path: str | None = None
    mime_type: str | None = None
    description: str | None = Field(
        default=None,
        description="Optional text description used by mocks when no real image pipeline exists.",
    )
