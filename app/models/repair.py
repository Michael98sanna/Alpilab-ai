"""Repair-session domain models.

These schemas are the intended data contract between Alpilab AI, Alpilab Check,
and Alpilab Hub. They are not backed by a database yet.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .common import SourceSystem, utcnow
from .device import Device


class RepairSessionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class MeasurementKind(str, Enum):
    VOLTAGE = "voltage"
    CURRENT = "current"
    RESISTANCE = "resistance"
    TEMPERATURE = "temperature"
    POWER = "power"
    OTHER = "other"


class RepairActionStatus(str, Enum):
    PROPOSED = "proposed"
    WAITING_CONFIRMATION = "waiting_confirmation"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class ImageKind(str, Enum):
    PHOTO = "photo"
    MICROSCOPE = "microscope"
    THERMAL = "thermal"
    ANNOTATED = "annotated"
    SCHEMATIC = "schematic"
    OTHER = "other"


class CustomerIssue(BaseModel):
    """What the customer reported, independent of lab findings."""

    id: UUID = Field(default_factory=uuid4)
    summary: str
    description: str | None = None
    reported_symptoms: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    previous_repair_notes: str | None = None


class DiagnosticTest(BaseModel):
    """A named diagnostic check and its outcome."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    category: str | None = None
    status: DiagnosticStatus = DiagnosticStatus.UNKNOWN
    details: str | None = None
    source: SourceSystem = SourceSystem.MANUAL
    performed_at: datetime | None = None


class Measurement(BaseModel):
    """A numeric reading from an instrument or a manual entry."""

    id: UUID = Field(default_factory=uuid4)
    kind: MeasurementKind
    value: float
    unit: str
    location: str | None = None
    source: SourceSystem = SourceSystem.MANUAL
    instrument: str | None = None
    taken_at: datetime = Field(default_factory=utcnow)


class Diagnosis(BaseModel):
    """A technical hypothesis. Facts and hypotheses must stay distinct."""

    id: UUID = Field(default_factory=uuid4)
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)


class RepairAction(BaseModel):
    """A proposed or executed repair step."""

    id: UUID = Field(default_factory=uuid4)
    description: str
    status: RepairActionStatus = RepairActionStatus.PROPOSED
    requires_confirmation: bool = False
    is_potentially_dangerous: bool = False
    permission_required: str | None = None


class RepairResult(BaseModel):
    """Outcome of a repair session or of a completed action set."""

    id: UUID = Field(default_factory=uuid4)
    success: bool
    summary: str
    remaining_issues: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None


class ImageAnnotation(BaseModel):
    """A future annotation on a repair photo. Coordinates are optional."""

    label: str
    note: str | None = None
    x: float | None = None
    y: float | None = None


class ImageAttachment(BaseModel):
    """Metadata for a stored image. Binary files belong in object storage."""

    id: UUID = Field(default_factory=uuid4)
    kind: ImageKind = ImageKind.PHOTO
    filename: str
    caption: str | None = None
    content_type: str | None = None
    storage_key: str | None = None
    annotations: list[ImageAnnotation] = Field(default_factory=list)
    source: SourceSystem = SourceSystem.ALPILAB_AI


class Note(BaseModel):
    """A free-text lab note attached to a session."""

    id: UUID = Field(default_factory=uuid4)
    content: str
    author: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class RepairSession(BaseModel):
    """Full snapshot of a repair job. Nested collections travel with the session."""

    id: UUID = Field(default_factory=uuid4)
    device: Device
    status: RepairSessionStatus = RepairSessionStatus.OPEN
    technician: str | None = None
    source: SourceSystem = SourceSystem.ALPILAB_AI
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    customer_issue: CustomerIssue | None = None
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    results: list[RepairResult] = Field(default_factory=list)
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
