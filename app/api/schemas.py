"""Shared HTTP API response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload for clients and load balancers."""

    status: str = "ok"
    service: str = "alpilab-ai"
    version: str = "0.1.0-foundation"
    ai_provider: str = "mock"


class ErrorResponse(BaseModel):
    """Standard API error envelope."""

    error: str
    detail: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
