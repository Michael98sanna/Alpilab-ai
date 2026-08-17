"""Pydantic request/response schemas for the HTTP API layer.

Domain models live in ``app.models``; these schemas shape public API payloads.
For this foundation phase they mostly re-export / wrap the domain models.
"""

from app.models.device import Device
from app.models.repair import (
    CustomerIssue,
    Diagnosis,
    DiagnosticTest,
    ImageAttachment,
    Measurement,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
)
from app.schemas.ai import AskRequest, AskResponse
from app.schemas.health import HealthResponse

__all__ = [
    "Device",
    "CustomerIssue",
    "DiagnosticTest",
    "Measurement",
    "Diagnosis",
    "RepairAction",
    "RepairResult",
    "ImageAttachment",
    "Note",
    "RepairSession",
    "AskRequest",
    "AskResponse",
    "HealthResponse",
]
