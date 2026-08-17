"""Domain data contracts for repairs and devices.

These models are the shared conceptual contract between:
- ALPILAB AI (cloud)
- ALPILAB CHECK (future bridge)
- ALPILAB HUB (future Windows bridge)

No live database persistence in this phase — schemas only.
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


class DeviceBrand(str, Enum):
    APPLE = "apple"
    SAMSUNG = "samsung"
    XIAOMI = "xiaomi"
    HUAWEI = "huawei"
    OPPO = "oppo"
    OTHER = "other"


class RepairSessionStatus(str, Enum):
    INTAKE = "intake"
    DIAGNOSING = "diagnosing"
    WAITING_PARTS = "waiting_parts"
    IN_REPAIR = "in_repair"
    TESTING = "testing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class Device(BaseModel):
    """Smartphone / tablet under repair."""

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
    created_at: datetime = Field(default_factory=_utcnow)


class CustomerIssue(BaseModel):
    """Problem as reported by the customer / intake."""

    id: str = Field(default_factory=_new_id)
    description: str
    reported_at: datetime = Field(default_factory=_utcnow)
    symptoms: list[str] = Field(default_factory=list)
    when_started: str | None = None
    liquid_damage_reported: bool = False
    prior_repair_reported: bool = False


class DiagnosticTest(BaseModel):
    """A single diagnostic check performed on the device."""

    id: str = Field(default_factory=_new_id)
    name: str
    category: str | None = None  # e.g. "display", "battery", "cellular"
    result: str
    passed: bool | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    performed_at: datetime = Field(default_factory=_utcnow)
    source: str | None = None  # e.g. "manual", "alpilab_check", "hub"


class Measurement(BaseModel):
    """Instrument reading (multimeter, power supply, thermal, …)."""

    id: str = Field(default_factory=_new_id)
    name: str
    value: float | str
    unit: str | None = None
    probe_point: str | None = None
    instrument: str | None = None  # multimeter | power_supply | thermal | …
    recorded_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Technical diagnosis with explicit confidence."""

    id: str = Field(default_factory=_new_id)
    summary: str
    root_cause_hypothesis: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    supporting_facts: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)


class RepairAction(BaseModel):
    """An action taken or planned during the repair."""

    id: str = Field(default_factory=_new_id)
    action: str
    status: str = "planned"  # planned | in_progress | done | skipped
    parts_used: list[str] = Field(default_factory=list)
    performed_by: str | None = None
    performed_at: datetime | None = None
    notes: str | None = None


class RepairResult(BaseModel):
    """Outcome of the repair session."""

    id: str = Field(default_factory=_new_id)
    success: bool
    summary: str
    verification_tests: list[str] = Field(default_factory=list)
    warranty_days: int | None = None
    completed_at: datetime = Field(default_factory=_utcnow)


class ImageAttachment(BaseModel):
    """Photo or annotated image linked to a repair session."""

    id: str = Field(default_factory=_new_id)
    filename: str
    content_type: str = "image/jpeg"
    storage_path: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    source: str | None = None  # camera | microscope | thermal | upload
    created_at: datetime = Field(default_factory=_utcnow)


class Note(BaseModel):
    """Free-form technician note."""

    id: str = Field(default_factory=_new_id)
    body: str
    author: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    tags: list[str] = Field(default_factory=list)


class RepairSession(BaseModel):
    """Aggregate root for a single repair job."""

    id: str = Field(default_factory=_new_id)
    device: Device
    customer_issue: CustomerIssue | None = None
    status: RepairSessionStatus = RepairSessionStatus.INTAKE
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    result: RepairResult | None = None
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    external_refs: dict[str, str] = Field(
        default_factory=dict
    )  # e.g. {"alpilab_check_id": "..."}
