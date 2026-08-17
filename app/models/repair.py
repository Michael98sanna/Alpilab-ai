"""Conceptual data models for devices, sessions, diagnostics and repairs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RepairSessionStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticTestStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MeasurementSource(StrEnum):
    MULTIMETER = "multimeter"
    POWER_SUPPLY = "power_supply"
    THERMAL_CAMERA = "thermal_camera"
    MICROSCOPE = "microscope"
    ALPILAB_CHECK = "alpilab_check"
    TECHNICIAN = "technician"
    OTHER = "other"


class RepairActionStatus(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RepairOutcome(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ImageKind(StrEnum):
    PHOTO = "photo"
    MICROSCOPE = "microscope"
    THERMAL = "thermal"
    ANNOTATED = "annotated"
    SCHEMATIC = "schematic"
    OTHER = "other"


class Device(BaseModel):
    """Physical device under repair. Identity fields are optional on purpose:
    a session can start before IMEI/serial are known.
    """

    id: UUID = Field(default_factory=uuid4)
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    model_code: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = Field(default=None, gt=0)
    os_name: str | None = None
    os_version: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)

    @field_validator("imei")
    @classmethod
    def imei_digits_only(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        compact = value.strip()
        if not compact.isdigit():
            raise ValueError("IMEI deve contenere solo cifre.")
        if len(compact) not in {14, 15, 16}:
            raise ValueError("IMEI deve avere 14, 15 o 16 cifre.")
        return compact


class CustomerIssue(BaseModel):
    """What the customer reports, before any bench measurement."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    description: str = Field(min_length=1)
    symptoms: list[str] = Field(default_factory=list)
    reported_by: str | None = None
    when_started: str | None = None
    reproducible: bool | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class DiagnosticTest(BaseModel):
    """A named check (hardware/software) with an outcome.

    `raw_payload` is an opaque bag for future Check/Hub data. Alpilab AI
    must not assume Alpilab Check internal structures.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    name: str = Field(min_length=1)
    category: str = "hardware"
    status: DiagnosticTestStatus = DiagnosticTestStatus.PENDING
    result_summary: str | None = None
    source: str | None = None
    raw_payload: dict[str, Any] | None = None
    performed_at: datetime | None = None


class Measurement(BaseModel):
    """A numeric reading (voltage, current, temperature, ...)."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    name: str = Field(min_length=1)
    source: MeasurementSource = MeasurementSource.TECHNICIAN
    value: float | None = None
    unit: str | None = None
    probe_point: str | None = None
    expected_min: float | None = None
    expected_max: float | None = None
    in_range: bool | None = None
    captured_at: datetime = Field(default_factory=_utcnow)


class Hypothesis(BaseModel):
    """A possible cause, never presented as a fact."""

    statement: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class Diagnosis(BaseModel):
    """Structured technical conclusion. Facts and hypotheses stay separate."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    summary: str = Field(min_length=1)
    facts: list[str] = Field(default_factory=list)
    detected_data: list[str] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=_utcnow)


class RepairAction(BaseModel):
    """A proposed or performed intervention on the device or the bench PC.

    Dangerous or irreversible actions must keep requires_confirmation=True
    until an operator sets confirmed=True.
    """

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    action_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    component: str | None = None
    requires_confirmation: bool = True
    confirmed: bool = False
    status: RepairActionStatus = RepairActionStatus.PROPOSED
    performed_by: str | None = None


class RepairResult(BaseModel):
    """Outcome of a session or of a single action."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    action_id: UUID | None = None
    outcome: RepairOutcome = RepairOutcome.UNKNOWN
    summary: str = Field(min_length=1)
    verified_by: str | None = None
    verified_at: datetime | None = None


class ImageAttachment(BaseModel):
    """Metadata for a stored image. File bytes are not handled in this phase."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    kind: ImageKind = ImageKind.PHOTO
    filename: str = Field(min_length=1)
    mime_type: str = "image/jpeg"
    storage_path: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Note(BaseModel):
    """Free-text note attached to a repair session."""

    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    content: str = Field(min_length=1)
    author: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class RepairSession(BaseModel):
    """Aggregate root for one repair job on one device."""

    id: UUID = Field(default_factory=uuid4)
    device: Device
    status: RepairSessionStatus = RepairSessionStatus.OPEN
    technician: str | None = None
    customer_issue: CustomerIssue | None = None
    tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    results: list[RepairResult] = Field(default_factory=list)
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
