"""Request/response schemas for the AI layer."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RequestKind(str, Enum):
    """Future router hints for provider selection."""

    GENERAL = "general"
    DIAGNOSIS = "diagnosis"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENTATION = "documentation"
    VOICE = "voice"


class RoutePreference(str, Enum):
    """Soft preferences the router may honor later."""

    AUTO = "auto"
    LOCAL = "local"
    CLOUD = "cloud"
    CHEAPEST = "cheapest"
    BEST_QUALITY = "best_quality"


class AIAskRequest(BaseModel):
    """API-facing ask payload."""

    prompt: str = Field(min_length=1)
    kind: RequestKind = RequestKind.GENERAL
    preference: RoutePreference = RoutePreference.AUTO
    has_images: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIAskResponse(BaseModel):
    """API-facing ask result."""

    answer: str
    provider: str
    model: str | None = None
    routed_as: str | None = None
