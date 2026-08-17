"""Domain models — conceptual contracts shared across AI, Check bridge, and Hub.

These are intentional data contracts. Persistence is not wired yet.
"""

from app.models.repair import (
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
