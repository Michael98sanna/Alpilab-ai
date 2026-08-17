"""API / transport schemas.

For phase 1, domain models double as the contract. This package exists
so future request/response DTOs can diverge from persistence models
without breaking imports.
"""

from app.models.domain import (
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
