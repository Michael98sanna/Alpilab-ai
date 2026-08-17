"""Shared request/response schemas for the AI layer."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RequestKind(str, Enum):
    """High-level request categories used by the future AI Router."""

    TEXT = "text"
    IMAGE = "image"
    DIAGNOSIS = "diagnosis"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class AIRequest(BaseModel):
    """Normalized input for any AI provider."""

    prompt: str = Field(..., min_length=1)
    kind: RequestKind = RequestKind.GENERAL
    image_paths: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class AIResponse(BaseModel):
    """Normalized output from any AI provider."""

    content: str
    provider: str
    kind: RequestKind = RequestKind.GENERAL
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score when the provider supplies one.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
