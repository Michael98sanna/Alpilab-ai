"""HTTP schemas for AI and health endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai.schemas import ImageInput


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    ai_provider: str
    environment: str


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    images: list[ImageInput] = Field(default_factory=list)
    preferred_provider: str | None = None


class GenerateResponse(BaseModel):
    text: str
    provider_name: str
    is_mock: bool
