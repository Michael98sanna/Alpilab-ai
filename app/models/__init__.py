"""Domain models that form the shared data contract.

These types are the intended contract between:
- Alpilab AI (cloud)
- Alpilab Check (future bridge)
- Alpilab Hub (future Windows service)

They are Pydantic models, not a live database. Persistence comes later.
"""

from .repair import (
    CustomerIssue,
    Device,
    Diagnosis,
    DiagnosticTest,
    DiagnosticTestStatus,
    Hypothesis,
    ImageAttachment,
    ImageKind,
    Measurement,
    MeasurementSource,
    Note,
    RepairAction,
    RepairActionStatus,
    RepairOutcome,
    RepairResult,
    RepairSession,
    RepairSessionStatus,
)

__all__ = [
    "CustomerIssue",
    "Device",
    "Diagnosis",
    "DiagnosticTest",
    "DiagnosticTestStatus",
    "Hypothesis",
    "ImageAttachment",
    "ImageKind",
    "Measurement",
    "MeasurementSource",
    "Note",
    "RepairAction",
    "RepairActionStatus",
    "RepairOutcome",
    "RepairResult",
    "RepairSession",
    "RepairSessionStatus",
]
