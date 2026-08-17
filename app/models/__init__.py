"""Domain models for repair workflow entities.

These models define the shared conceptual contract between:
- Alpilab AI
- future Alpilab Check bridge
- future Alpilab Hub

No database persistence is wired yet — schemas are the source of truth.
"""

from app.models.device import Device
from app.models.repair import (
    CustomerIssue,
    Diagnosis,
    DiagnosticTest,
    DiagnosticTestStatus,
    ImageAttachment,
    Measurement,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
    SessionStatus,
)

__all__ = [
    "Device",
    "CustomerIssue",
    "DiagnosticTest",
    "DiagnosticTestStatus",
    "Measurement",
    "Diagnosis",
    "RepairAction",
    "RepairResult",
    "ImageAttachment",
    "Note",
    "RepairSession",
    "SessionStatus",
]
