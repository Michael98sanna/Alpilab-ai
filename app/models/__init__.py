"""
Conceptual domain models for repair workflows.

These define the shared data contract between:
- Alpilab AI
- future Alpilab Check bridge
- future Alpilab Hub

No persistent database is required in this foundation phase.
Schemas live in app.schemas; models here are domain aliases / helpers.
"""

from app.schemas.repair import (
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
    "CustomerIssue",
    "Device",
    "Diagnosis",
    "DiagnosticTest",
    "ImageAttachment",
    "Measurement",
    "Note",
    "RepairAction",
    "RepairResult",
    "RepairSession",
]
