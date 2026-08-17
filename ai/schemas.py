"""Shared request/response types for the AI layer.

The rest of the application depends on these types, not on any vendor SDK.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ImageReference(BaseModel):
    """Pointer to an image. Binary upload/storage is not implemented yet."""

    filename: str
    mime_type: str = "image/jpeg"
    storage_path: str | None = None
    caption: str | None = None


class GenerationRequest(BaseModel):
    """A text generation request independent of the backend model."""

    prompt: str = Field(min_length=1)
    system_prompt: str | None = None
    context: dict[str, Any] | None = None
    max_tokens: int | None = Field(default=None, gt=0)


class ImageGenerationRequest(GenerationRequest):
    """Text + image request. Image analysis is not implemented in this phase."""

    images: list[ImageReference] = Field(min_length=1)


class GenerationResponse(BaseModel):
    """Normalized AI output.

    Technical answers should separate facts, detected data, hypotheses
    and confidence. The mock provider fills these honestly as placeholders.
    """

    text: str
    provider_name: str
    is_mock: bool = False
    facts: list[str] = Field(default_factory=list)
    detected_data: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
