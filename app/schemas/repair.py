"""
Repair-domain schemas.

These models are the conceptual contract for devices, sessions, diagnostics,
measurements, actions and results. Persistence is intentionally deferred.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class DeviceBrand(str, Enum):
    APPLE = "apple"
    SAMSUNG = "samsung"
    XIAOMI = "xiaomi"
    HUAWEI = "huawei"
    OPPO = "oppo"
    OTHER = "other"


class RepairSessionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticTestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class MeasurementUnit(str, Enum):
    VOLT = "V"
    MILLIVOLT = "mV"
    AMPERE = "A"
    MILLIAMPERE = "mA"
    OHM = "ohm"
    CELSIUS = "C"
    OTHER = "other"


class Device(BaseModel):
    """Smartphone / device under repair."""

    id: str = Field(default_factory=_new_id)
    brand: DeviceBrand = DeviceBrand.OTHER
    model: str
    model_code: str | None = None
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    os_version: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerIssue(BaseModel):
    """Customer-reported problem description."""

    id: str = Field(default_factory=_new_id)
    summary: str
    description: str | None = None
    reported_at: datetime = Field(default_factory=_utc_now)
    symptoms: list[str] = Field(default_factory=list)


class DiagnosticTest(BaseModel):
    """A single diagnostic check performed on a device."""

    id: str = Field(default_factory=_new_id)
    name: str
    category: str | None = None
    status: DiagnosticTestStatus = DiagnosticTestStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_summary: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    source: str | None = Field(
        default=None,
        description="Origin of the test, e.g. manual | alpilab_check | hub",
    )


class Measurement(BaseModel):
    """Numeric measurement from bench tools (multimeter, PSU, thermal, etc.)."""

    id: str = Field(default_factory=_new_id)
    label: str
    value: float
    unit: MeasurementUnit = MeasurementUnit.OTHER
    probe_point: str | None = None
    recorded_at: datetime = Field(default_factory=_utc_now)
    instrument: str | None = Field(
        default=None,
        description="Instrument that produced the value, e.g. multimeter | power_supply",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Technical diagnosis with explicit confidence."""

    id: str = Field(default_factory=_new_id)
    title: str
    summary: str
    root_cause: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)


class RepairAction(BaseModel):
    """An action taken or planned during repair."""

    id: str = Field(default_factory=_new_id)
    title: str
    description: str | None = None
    requires_confirmation: bool = Field(
        default=False,
        description="Dangerous or irreversible actions must require explicit confirmation.",
    )
    confirmed: bool = False
    performed_at: datetime | None = None
    performer: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairResult(BaseModel):
    """Outcome of a repair session or action set."""

    id: str = Field(default_factory=_new_id)
    success: bool
    summary: str
    remaining_issues: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=_utc_now)


class ImageAttachment(BaseModel):
    """Photo or annotated image related to a repair."""

    id: str = Field(default_factory=_new_id)
    filename: str
    path: str | None = None
    mime_type: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    captured_at: datetime = Field(default_factory=_utc_now)
    source: str | None = Field(
        default=None,
        description="e.g. camera | microscope | thermal | upload",
    )


class Note(BaseModel):
    """Free-form technician note."""

    id: str = Field(default_factory=_new_id)
    content: str
    author: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    tags: list[str] = Field(default_factory=list)


class RepairSession(BaseModel):
    """
    Aggregate root for a repair job.

    Holds device context plus related issues, tests, measurements, diagnoses,
    actions, results, images and notes.
    """

    id: str = Field(default_factory=_new_id)
    status: RepairSessionStatus = RepairSessionStatus.OPEN
    device: Device
    customer_issue: CustomerIssue | None = None
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    results: list[RepairResult] = Field(default_factory=list)
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    technician: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
