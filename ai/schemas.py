"""Shared request/response contracts for the AI layer.

These schemas isolate the rest of the application from provider-specific
payload formats. Future providers must adapt to these contracts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RequestKind(str, Enum):
    """High-level request categories used by the router for future routing."""

    TEXT = "text"
    IMAGE = "image"
    DIAGNOSIS = "diagnosis"
    GUIDED = "guided"
    GENERAL = "general"


class RoutingHints(BaseModel):
    """Optional hints for future AI Router decisions.

    Not all fields are used yet. They document the intended selection
    criteria (cost, capability, availability, images, fallback).
    """

    kind: RequestKind = RequestKind.GENERAL
    prefer_local: bool = False
    prefer_cloud: bool = False
    allow_fallback: bool = True
    requires_image: bool = False
    max_cost_tier: str | None = None  # e.g. "free", "low", "standard"
    required_capabilities: list[str] = Field(default_factory=list)


class AIMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str


class AIGenerateRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    messages: list[AIMessage] = Field(default_factory=list)
    hints: RoutingHints = Field(default_factory=RoutingHints)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIImageGenerateRequest(BaseModel):
    prompt: str
    image_path: str | None = None
    image_bytes_b64: str | None = None
    system_prompt: str | None = None
    hints: RoutingHints = Field(
        default_factory=lambda: RoutingHints(
            kind=RequestKind.IMAGE,
            requires_image=True,
        )
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIGenerateResponse(BaseModel):
    """Provider-agnostic generation result."""

    content: str
    provider: str
    model: str | None = None
    is_mock: bool = False
    finish_reason: str | None = None
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
