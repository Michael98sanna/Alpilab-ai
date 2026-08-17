"""Repair-session domain models.

These are conceptual contracts — persistence and Check/Hub adapters come later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class SessionStatus(str, Enum):
    INTAKE = "intake"
    DIAGNOSING = "diagnosing"
    WAITING_PARTS = "waiting_parts"
    REPAIRING = "repairing"
    TESTING = "testing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticTestStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CustomerIssue(BaseModel):
    """Problem as reported by the customer / intake desk."""

    id: str = Field(default_factory=_new_id)
    description: str
    reported_at: datetime = Field(default_factory=_utcnow)
    symptoms: list[str] = Field(default_factory=list)
    when_started: str | None = None
    previous_repairs: str | None = None


class DiagnosticTest(BaseModel):
    """A named diagnostic check performed during the session."""

    id: str = Field(default_factory=_new_id)
    name: str
    status: DiagnosticTestStatus = DiagnosticTestStatus.PENDING
    procedure: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    performed_at: datetime | None = None
    notes: str | None = None


class Measurement(BaseModel):
    """Numeric or textual measurement from instruments (future Hub)."""

    id: str = Field(default_factory=_new_id)
    name: str
    value: str
    unit: str | None = None
    instrument: str | None = Field(
        default=None,
        description="e.g. multimeter, power_supply, thermal_camera — conceptual only.",
    )
    recorded_at: datetime = Field(default_factory=_utcnow)
    notes: str | None = None


class Diagnosis(BaseModel):
    """Technical conclusion proposed by technician and/or AI."""

    id: str = Field(default_factory=_new_id)
    summary: str
    root_cause: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    evidence: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    source: str = Field(
        default="technician",
        description="technician | ai | check_bridge | hub",
    )


class RepairAction(BaseModel):
    """A concrete repair step performed or planned."""

    id: str = Field(default_factory=_new_id)
    description: str
    status: str = "planned"  # planned | in_progress | done | skipped
    parts_used: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class RepairResult(BaseModel):
    """Outcome of the repair session."""

    id: str = Field(default_factory=_new_id)
    success: bool
    summary: str
    verified_tests: list[str] = Field(default_factory=list)
    remaining_issues: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=_utcnow)


class ImageAttachment(BaseModel):
    """Photo or annotated image linked to a repair session."""

    id: str = Field(default_factory=_new_id)
    filename: str
    path: str
    caption: str | None = None
    kind: str = Field(
        default="photo",
        description="photo | annotated | microscope | thermal | schematic",
    )
    created_at: datetime = Field(default_factory=_utcnow)


class Note(BaseModel):
    """Free-form lab note."""

    id: str = Field(default_factory=_new_id)
    content: str
    author: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    tags: list[str] = Field(default_factory=list)


class RepairSession(BaseModel):
    """Aggregate root for a single repair job."""

    id: str = Field(default_factory=_new_id)
    device_id: str
    status: SessionStatus = SessionStatus.INTAKE
    customer_issue: CustomerIssue | None = None
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    result: RepairResult | None = None
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    opened_at: datetime = Field(default_factory=_utcnow)
    closed_at: datetime | None = None
    technician: str | None = None
