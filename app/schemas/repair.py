"""Domain data contracts for Alpilab AI.

These schemas are the shared conceptual contract for future exchange with
Alpilab Check and Alpilab Hub. They are not yet persisted to a database.
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


class RepairStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    DIAGNOSED = "diagnosed"
    REPAIRED = "repaired"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Device(BaseModel):
    """Smartphone / board under repair."""

    id: str = Field(default_factory=_new_id)
    brand: str
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
    """Problem as reported by the customer."""

    id: str = Field(default_factory=_new_id)
    summary: str
    description: str | None = None
    reported_at: datetime = Field(default_factory=_utcnow)
    symptoms: list[str] = Field(default_factory=list)


class DiagnosticTest(BaseModel):
    """A check performed during diagnosis (software or hardware)."""

    id: str = Field(default_factory=_new_id)
    name: str
    category: str | None = None
    result: str | None = None
    passed: bool | None = None
    performed_at: datetime = Field(default_factory=_utcnow)
    raw_data: dict[str, Any] = Field(default_factory=dict)


class Measurement(BaseModel):
    """Numeric reading from multimeter, power supply, thermal camera, etc."""

    id: str = Field(default_factory=_new_id)
    source: str  # e.g. multimeter, power_supply, thermal_camera
    label: str
    value: float
    unit: str
    measured_at: datetime = Field(default_factory=_utcnow)
    context: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Technical conclusion (hypothesis or confirmed fault)."""

    id: str = Field(default_factory=_new_id)
    summary: str
    details: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_confirmed: bool = False
    related_component: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class RepairAction(BaseModel):
    """Work performed or planned on the device."""

    id: str = Field(default_factory=_new_id)
    action: str
    details: str | None = None
    performed_by: str | None = None
    performed_at: datetime | None = None
    requires_confirmation: bool = False
    confirmed: bool = False


class RepairResult(BaseModel):
    """Outcome after repair actions."""

    id: str = Field(default_factory=_new_id)
    success: bool
    summary: str
    remaining_issues: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=_utcnow)


class ImageAttachment(BaseModel):
    """Reference to a stored photo / annotated image (storage path later)."""

    id: str = Field(default_factory=_new_id)
    filename: str
    content_type: str = "image/jpeg"
    storage_key: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)


class Note(BaseModel):
    """Free-form technician note."""

    id: str = Field(default_factory=_new_id)
    author: str | None = None
    body: str
    created_at: datetime = Field(default_factory=_utcnow)
    tags: list[str] = Field(default_factory=list)


class RepairSession(BaseModel):
    """Full repair case: the main aggregate for lab history."""

    id: str = Field(default_factory=_new_id)
    device: Device
    customer_issue: CustomerIssue
    status: RepairStatus = RepairStatus.OPEN
    opened_at: datetime = Field(default_factory=_utcnow)
    closed_at: datetime | None = None
    technician: str | None = None
    diagnostic_tests: list[DiagnosticTest] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    actions: list[RepairAction] = Field(default_factory=list)
    results: list[RepairResult] = Field(default_factory=list)
    images: list[ImageAttachment] = Field(default_factory=list)
    notes: list[Note] = Field(default_factory=list)
    external_refs: dict[str, str] = Field(
        default_factory=dict,
        description="Future IDs from Alpilab Check / Hub / third-party tools.",
    )
