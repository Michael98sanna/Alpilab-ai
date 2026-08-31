"""Shared schemas for AI requests and responses."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AIMessageRole(str, Enum):
    """Role of a message in an AI conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIMessage(BaseModel):
    """A single message in an AI conversation."""

    role: AIMessageRole
    content: str


class ImageInput(BaseModel):
    """Reference to an image for multimodal generation."""

    reference: str = Field(
        description="Path, URL, or opaque identifier for the image payload."
    )
    mime_type: str = Field(default="image/jpeg")
    description: str | None = Field(
        default=None,
        description="Optional human-readable description of the image.",
    )


class AIRequest(BaseModel):
    """Provider-agnostic request sent through the AI router."""

    prompt: str
    messages: list[AIMessage] = Field(default_factory=list)
    images: list[ImageInput] = Field(default_factory=list)
    system_prompt: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1)
    symptom: str | None = Field(
        default=None,
        description="Optional symptom text for knowledge-base RAG retrieval.",
    )
    device: str | None = Field(
        default=None,
        description="Optional device model filter for RAG retrieval.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    """Provider-agnostic response from an AI generation call."""

    content: str
    provider: str
    model: str = ""
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderCapability(str, Enum):
    """Capabilities that providers may advertise for routing."""

    TEXT_GENERATION = "text_generation"
    IMAGE_INPUT = "image_input"
    STREAMING = "streaming"
    LOCAL = "local"
    CLOUD = "cloud"
