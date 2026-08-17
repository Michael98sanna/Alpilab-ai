"""Repair-domain conceptual models (no live database in this phase)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class DeviceType(str, Enum):
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    OTHER = "other"


class SessionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_PARTS = "waiting_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"


# Backward-compatible alias (avoid pytest collecting *Test* classes).
TestStatus = DiagnosticStatus
DiagnosticStatus.__test__ = False  # type: ignore[attr-defined]
TestStatus.__test__ = False  # type: ignore[attr-defined]


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


@dataclass
class Device:
    """Physical device under repair."""

    brand: str
    model: str
    id: str = field(default_factory=_new_id)
    device_type: DeviceType = DeviceType.SMARTPHONE
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    os_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def display_name(self) -> str:
        return f"{self.brand} {self.model}".strip()


@dataclass
class CustomerIssue:
    """Customer-reported problem for a repair session."""

    description: str
    id: str = field(default_factory=_new_id)
    reported_at: datetime = field(default_factory=_utcnow)
    symptoms: list[str] = field(default_factory=list)
    when_started: str | None = None
    liquid_damage_suspected: bool = False
    previous_repairs: str | None = None


@dataclass
class DiagnosticTest:
    """A diagnostic check performed (or planned) during a session."""

    name: str
    id: str = field(default_factory=_new_id)
    status: DiagnosticStatus = DiagnosticStatus.PENDING
    procedure: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    performed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Measurement:
    """Numeric or textual measurement from tools (multimeter, PSU, etc.)."""

    name: str
    value: str
    id: str = field(default_factory=_new_id)
    unit: str | None = None
    source: str | None = None  # e.g. "multimeter", "power_supply", "manual"
    measured_at: datetime = field(default_factory=_utcnow)
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Diagnosis:
    """Technical diagnosis with explicit confidence."""

    summary: str
    id: str = field(default_factory=_new_id)
    root_cause: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    facts: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)


@dataclass
class RepairAction:
    """An action taken (or planned) on the device."""

    description: str
    id: str = field(default_factory=_new_id)
    parts_used: list[str] = field(default_factory=list)
    performed_at: datetime | None = None
    technician: str | None = None
    dangerous: bool = False
    confirmed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairResult:
    """Outcome of a repair session or action set."""

    success: bool
    id: str = field(default_factory=_new_id)
    summary: str = ""
    verified_tests: list[str] = field(default_factory=list)
    remaining_issues: list[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=_utcnow)


@dataclass
class ImageAttachment:
    """Photo or annotated image related to a repair."""

    filename: str
    id: str = field(default_factory=_new_id)
    path: str | None = None
    content_type: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] = field(default_factory=list)
    captured_at: datetime = field(default_factory=_utcnow)
    source: str | None = None  # e.g. "camera", "microscope", "thermal"


@dataclass
class Note:
    """Free-form lab note."""

    content: str
    id: str = field(default_factory=_new_id)
    author: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    tags: list[str] = field(default_factory=list)


@dataclass
class RepairSession:
    """Central aggregate linking device, issue, tests, diagnosis, and results."""

    device: Device
    issue: CustomerIssue
    id: str = field(default_factory=_new_id)
    status: SessionStatus = SessionStatus.OPEN
    opened_at: datetime = field(default_factory=_utcnow)
    closed_at: datetime | None = None
    technician: str | None = None
    tests: list[DiagnosticTest] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    diagnoses: list[Diagnosis] = field(default_factory=list)
    actions: list[RepairAction] = field(default_factory=list)
    results: list[RepairResult] = field(default_factory=list)
    images: list[ImageAttachment] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_test(self, test: DiagnosticTest) -> None:
        self.tests.append(test)

    def add_measurement(self, measurement: Measurement) -> None:
        self.measurements.append(measurement)

    def add_note(self, note: Note) -> None:
        self.notes.append(note)
