"""Domain models — shared conceptual contract for Alpilab AI / Check / Hub.

These are in-memory / schema-oriented models for the foundation phase.
Persistence (PostgreSQL / SQLite) will be added later without changing the
public field contracts when possible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class DeviceType(str, Enum):
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    OTHER = "other"


class RepairStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    WAITING_CUSTOMER = "waiting_customer"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    NOT_RUN = "not_run"


class MeasurementUnit(str, Enum):
    VOLT = "V"
    AMPERE = "A"
    OHM = "Ohm"
    CELSIUS = "C"
    OTHER = "other"


class Device(BaseModel):
    """Physical device under repair."""

    id: str = Field(default_factory=_new_id)
    brand: str
    model: str
    device_type: DeviceType = DeviceType.SMARTPHONE
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerIssue(BaseModel):
    """Issue as reported by the customer / intake."""

    id: str = Field(default_factory=_new_id)
    summary: str
    description: str | None = None
    reported_at: datetime = Field(default_factory=_utcnow)
    symptoms: list[str] = Field(default_factory=list)


class DiagnosticTest(BaseModel):
    """A diagnostic check performed on the device."""

    id: str = Field(default_factory=_new_id)
    name: str
    status: DiagnosticResultStatus = DiagnosticResultStatus.NOT_RUN
    performed_at: datetime | None = None
    details: str | None = None
    source: str | None = None  # e.g. "manual", "alpilab_check", "hub"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Measurement(BaseModel):
    """Numeric measurement from bench tools (multimeter, PSU, thermal, …)."""

    id: str = Field(default_factory=_new_id)
    name: str
    value: float
    unit: MeasurementUnit = MeasurementUnit.OTHER
    probe_point: str | None = None
    measured_at: datetime = Field(default_factory=_utcnow)
    source: str | None = None
    notes: str | None = None


class Diagnosis(BaseModel):
    """Technical diagnosis proposed or confirmed by a technician / AI."""

    id: str = Field(default_factory=_new_id)
    summary: str
    root_cause: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    hypotheses: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    created_by: str | None = None  # "technician" | "ai" | user id later
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairAction(BaseModel):
    """An action performed during the repair."""

    id: str = Field(default_factory=_new_id)
    description: str
    performed_at: datetime = Field(default_factory=_utcnow)
    performed_by: str | None = None
    parts_used: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairResult(BaseModel):
    """Outcome of a repair session."""

    id: str = Field(default_factory=_new_id)
    success: bool
    summary: str
    completed_at: datetime = Field(default_factory=_utcnow)
    follow_up: str | None = None
    warranty_days: int | None = None


class ImageAttachment(BaseModel):
    """Photo or annotated image linked to a repair session."""

    id: str = Field(default_factory=_new_id)
    filename: str
    path: str | None = None  # storage path / URI — not loaded here
    caption: str | None = None
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    captured_at: datetime = Field(default_factory=_utcnow)
    source: str | None = None  # "camera" | "microscope" | "thermal" | …


class Note(BaseModel):
    """Free-form note attached to a repair session."""

    id: str = Field(default_factory=_new_id)
    content: str
    created_at: datetime = Field(default_factory=_utcnow)
    author: str | None = None
    tags: list[str] = Field(default_factory=list)


class RepairSession(BaseModel):
    """Full repair session aggregating device, diagnostics, actions, media."""

    id: str = Field(default_factory=_new_id)
    device: Device
    status: RepairStatus = RepairStatus.OPEN
    customer_issue: CustomerIssue | None = None
    opened_at: datetime = Field(default_factory=_utcnow)
    closed_at: datetime | None = None
    technician: str | None = None
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    result: RepairResult | None = None
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(default_factory=dict)
    # e.g. {"alpilab_check_job_id": "..."} — bridge identifiers only
