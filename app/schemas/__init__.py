"""API / transport schemas (request & response DTOs).

Domain models live in ``app.models``. These schemas are for HTTP boundaries
and can evolve independently when the API is expanded.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ai.schemas import RequestKind


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "Alpilab AI"
    ai_provider: str
    ready: bool = True


class AskRequest(BaseModel):
    prompt: str = Field(min_length=1)
    kind: RequestKind = RequestKind.GENERAL
    image_paths: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AskResponse(BaseModel):
    content: str
    provider: str
    model: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# Re-export domain models that act as shared contracts for Check / Hub.
from app.models import (  # noqa: E402
    CustomerIssue,
    Device,
    Diagnosis,
    DiagnosticTest,
    ImageAttachment,
    Measurement,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
)

__all__ = [
    "AskRequest",
    "AskResponse",
    "CustomerIssue",
    "Device",
    "Diagnosis",
    "DiagnosticTest",
    "HealthResponse",
    "ImageAttachment",
    "Measurement",
    "Note",
    "RepairAction",
    "RepairResult",
    "RepairSession",
]
