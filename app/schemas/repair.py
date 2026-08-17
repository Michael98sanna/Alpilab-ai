"""Pydantic schemas for repair domain entities."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import (
    DiagnosisConfidence,
    DiagnosticTestStatus,
    ImageAttachmentKind,
    RepairResultStatus,
    RepairSessionStatus,
)


class Device(BaseModel):
    """Smartphone or device under repair."""

    id: str
    brand: str
    model: str
    variant: str | None = None
    serial_number: str | None = None
    imei: str | None = None
    color: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerIssue(BaseModel):
    """Problem reported by the customer."""

    id: str
    repair_session_id: str
    description: str
    reported_at: datetime | None = None
    symptoms: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiagnosticTest(BaseModel):
    """A verifiable diagnostic check performed on the device."""

    id: str
    repair_session_id: str
    name: str
    description: str | None = None
    status: DiagnosticTestStatus = DiagnosticTestStatus.PENDING
    procedure: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    performed_at: datetime | None = None
    performed_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Measurement(BaseModel):
    """Numeric or structured measurement captured during diagnostics."""

    id: str
    repair_session_id: str
    source: str = Field(description="e.g. multimeter, power_supply, thermal_camera")
    label: str
    value: float | str
    unit: str | None = None
    recorded_at: datetime | None = None
    diagnostic_test_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    """Technical hypothesis or conclusion about the fault."""

    id: str
    repair_session_id: str
    summary: str
    details: str | None = None
    confidence: DiagnosisConfidence = DiagnosisConfidence.MEDIUM
    supporting_test_ids: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairAction(BaseModel):
    """Repair step performed or planned."""

    id: str
    repair_session_id: str
    description: str
    parts_used: list[str] = Field(default_factory=list)
    performed_at: datetime | None = None
    performed_by: str | None = None
    requires_confirmation: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairResult(BaseModel):
    """Final outcome of the repair session."""

    id: str
    repair_session_id: str
    status: RepairResultStatus = RepairResultStatus.NOT_ATTEMPTED
    summary: str | None = None
    verified_tests: list[str] = Field(default_factory=list)
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ImageAttachment(BaseModel):
    """Photo or scan linked to a repair session."""

    id: str
    repair_session_id: str
    kind: ImageAttachmentKind = ImageAttachmentKind.OTHER
    storage_reference: str = Field(
        description="Future object storage key or local path reference."
    )
    caption: str | None = None
    captured_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Note(BaseModel):
    """Free-form technician note."""

    id: str
    repair_session_id: str
    content: str
    author: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepairSession(BaseModel):
    """Container for the full repair workflow."""

    id: str
    device_id: str
    status: RepairSessionStatus = RepairSessionStatus.OPEN
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    technician_id: str | None = None
    customer_issue_ids: list[str] = Field(default_factory=list)
    diagnostic_test_ids: list[str] = Field(default_factory=list)
    measurement_ids: list[str] = Field(default_factory=list)
    diagnosis_ids: list[str] = Field(default_factory=list)
    repair_action_ids: list[str] = Field(default_factory=list)
    image_attachment_ids: list[str] = Field(default_factory=list)
    note_ids: list[str] = Field(default_factory=list)
    repair_result_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
