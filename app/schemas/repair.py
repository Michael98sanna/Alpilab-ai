"""Serializable schemas mirroring domain models.

These define the shared contract for future Alpilab AI / Check / Hub exchange.
No ORM or database binding in this phase — plain dataclasses with to/from dict.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from uuid import uuid4

from app.models.repair import (
    ConfidenceLevel,
    CustomerIssue,
    Device,
    DeviceType,
    Diagnosis,
    DiagnosticStatus,
    DiagnosticTest,
    Measurement,
    RepairSession,
    SessionStatus,
)


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _id_or_new(value: str | None) -> str:
    return value or str(uuid4())


@dataclass
class DeviceSchema:
    brand: str
    model: str
    id: str | None = None
    device_type: str = DeviceType.SMARTPHONE.value
    imei: str | None = None
    serial_number: str | None = None
    color: str | None = None
    storage_gb: int | None = None
    os_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model(self) -> Device:
        return Device(
            id=_id_or_new(self.id),
            brand=self.brand,
            model=self.model,
            device_type=DeviceType(self.device_type),
            imei=self.imei,
            serial_number=self.serial_number,
            color=self.color,
            storage_gb=self.storage_gb,
            os_version=self.os_version,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_model(cls, device: Device) -> "DeviceSchema":
        return cls(
            id=device.id,
            brand=device.brand,
            model=device.model,
            device_type=device.device_type.value,
            imei=device.imei,
            serial_number=device.serial_number,
            color=device.color,
            storage_gb=device.storage_gb,
            os_version=device.os_version,
            metadata=dict(device.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceSchema":
        return cls(
            id=data.get("id"),
            brand=data["brand"],
            model=data["model"],
            device_type=data.get("device_type", DeviceType.SMARTPHONE.value),
            imei=data.get("imei"),
            serial_number=data.get("serial_number"),
            color=data.get("color"),
            storage_gb=data.get("storage_gb"),
            os_version=data.get("os_version"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class CustomerIssueSchema:
    description: str
    id: str | None = None
    reported_at: str | None = None
    symptoms: list[str] = field(default_factory=list)
    when_started: str | None = None
    liquid_damage_suspected: bool = False
    previous_repairs: str | None = None

    def to_model(self) -> CustomerIssue:
        from datetime import timezone

        return CustomerIssue(
            id=_id_or_new(self.id),
            description=self.description,
            reported_at=_parse_dt(self.reported_at)
            or datetime.now(timezone.utc),
            symptoms=list(self.symptoms),
            when_started=self.when_started,
            liquid_damage_suspected=self.liquid_damage_suspected,
            previous_repairs=self.previous_repairs,
        )

    @classmethod
    def from_model(cls, issue: CustomerIssue) -> "CustomerIssueSchema":
        return cls(
            id=issue.id,
            description=issue.description,
            reported_at=issue.reported_at.isoformat(),
            symptoms=list(issue.symptoms),
            when_started=issue.when_started,
            liquid_damage_suspected=issue.liquid_damage_suspected,
            previous_repairs=issue.previous_repairs,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosticTestSchema:
    name: str
    id: str | None = None
    status: str = DiagnosticStatus.PENDING.value
    procedure: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    performed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model(self) -> DiagnosticTest:
        return DiagnosticTest(
            id=_id_or_new(self.id),
            name=self.name,
            status=DiagnosticStatus(self.status),
            procedure=self.procedure,
            expected_result=self.expected_result,
            actual_result=self.actual_result,
            performed_at=_parse_dt(self.performed_at),
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_model(cls, test: DiagnosticTest) -> "DiagnosticTestSchema":
        return cls(
            id=test.id,
            name=test.name,
            status=test.status.value,
            procedure=test.procedure,
            expected_result=test.expected_result,
            actual_result=test.actual_result,
            performed_at=test.performed_at.isoformat() if test.performed_at else None,
            metadata=dict(test.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MeasurementSchema:
    name: str
    value: str
    id: str | None = None
    unit: str | None = None
    source: str | None = None
    measured_at: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model(self) -> Measurement:
        from datetime import timezone

        return Measurement(
            id=_id_or_new(self.id),
            name=self.name,
            value=self.value,
            unit=self.unit,
            source=self.source,
            measured_at=_parse_dt(self.measured_at)
            or datetime.now(timezone.utc),
            notes=self.notes,
            metadata=dict(self.metadata),
        )

    @classmethod
    def from_model(cls, measurement: Measurement) -> "MeasurementSchema":
        return cls(
            id=measurement.id,
            name=measurement.name,
            value=measurement.value,
            unit=measurement.unit,
            source=measurement.source,
            measured_at=measurement.measured_at.isoformat(),
            notes=measurement.notes,
            metadata=dict(measurement.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnosisSchema:
    summary: str
    id: str | None = None
    root_cause: str | None = None
    confidence: str = ConfidenceLevel.LOW.value
    facts: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    recommended_tests: list[str] = field(default_factory=list)
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_model(cls, diagnosis: Diagnosis) -> "DiagnosisSchema":
        return cls(
            id=diagnosis.id,
            summary=diagnosis.summary,
            root_cause=diagnosis.root_cause,
            confidence=diagnosis.confidence.value,
            facts=list(diagnosis.facts),
            hypotheses=list(diagnosis.hypotheses),
            recommended_tests=list(diagnosis.recommended_tests),
            created_at=diagnosis.created_at.isoformat(),
        )


@dataclass
class RepairActionSchema:
    description: str
    id: str | None = None
    parts_used: list[str] = field(default_factory=list)
    performed_at: str | None = None
    technician: str | None = None
    dangerous: bool = False
    confirmed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairResultSchema:
    success: bool
    id: str | None = None
    summary: str = ""
    verified_tests: list[str] = field(default_factory=list)
    remaining_issues: list[str] = field(default_factory=list)
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImageAttachmentSchema:
    filename: str
    id: str | None = None
    path: str | None = None
    content_type: str | None = None
    caption: str | None = None
    annotations: list[dict[str, Any]] = field(default_factory=list)
    captured_at: str | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NoteSchema:
    content: str
    id: str | None = None
    author: str | None = None
    created_at: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairSessionSchema:
    device: DeviceSchema
    issue: CustomerIssueSchema
    id: str | None = None
    status: str = SessionStatus.OPEN.value
    opened_at: str | None = None
    closed_at: str | None = None
    technician: str | None = None
    tests: list[DiagnosticTestSchema] = field(default_factory=list)
    measurements: list[MeasurementSchema] = field(default_factory=list)
    diagnoses: list[DiagnosisSchema] = field(default_factory=list)
    actions: list[RepairActionSchema] = field(default_factory=list)
    results: list[RepairResultSchema] = field(default_factory=list)
    images: list[ImageAttachmentSchema] = field(default_factory=list)
    notes: list[NoteSchema] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model(self) -> RepairSession:
        from datetime import timezone

        session = RepairSession(
            id=_id_or_new(self.id),
            device=self.device.to_model(),
            issue=self.issue.to_model(),
            status=SessionStatus(self.status),
            opened_at=_parse_dt(self.opened_at) or datetime.now(timezone.utc),
            closed_at=_parse_dt(self.closed_at),
            technician=self.technician,
            metadata=dict(self.metadata),
        )
        for test in self.tests:
            session.add_test(test.to_model())
        for measurement in self.measurements:
            session.add_measurement(measurement.to_model())
        return session

    @classmethod
    def from_model(cls, session: RepairSession) -> "RepairSessionSchema":
        return cls(
            id=session.id,
            device=DeviceSchema.from_model(session.device),
            issue=CustomerIssueSchema.from_model(session.issue),
            status=session.status.value,
            opened_at=session.opened_at.isoformat(),
            closed_at=session.closed_at.isoformat() if session.closed_at else None,
            technician=session.technician,
            tests=[DiagnosticTestSchema.from_model(t) for t in session.tests],
            measurements=[
                MeasurementSchema.from_model(m) for m in session.measurements
            ],
            diagnoses=[DiagnosisSchema.from_model(d) for d in session.diagnoses],
            actions=[
                RepairActionSchema(
                    id=a.id,
                    description=a.description,
                    parts_used=list(a.parts_used),
                    performed_at=a.performed_at.isoformat() if a.performed_at else None,
                    technician=a.technician,
                    dangerous=a.dangerous,
                    confirmed=a.confirmed,
                    metadata=dict(a.metadata),
                )
                for a in session.actions
            ],
            results=[
                RepairResultSchema(
                    id=r.id,
                    success=r.success,
                    summary=r.summary,
                    verified_tests=list(r.verified_tests),
                    remaining_issues=list(r.remaining_issues),
                    completed_at=r.completed_at.isoformat(),
                )
                for r in session.results
            ],
            images=[
                ImageAttachmentSchema(
                    id=img.id,
                    filename=img.filename,
                    path=img.path,
                    content_type=img.content_type,
                    caption=img.caption,
                    annotations=list(img.annotations),
                    captured_at=img.captured_at.isoformat(),
                    source=img.source,
                )
                for img in session.images
            ],
            notes=[
                NoteSchema(
                    id=n.id,
                    content=n.content,
                    author=n.author,
                    created_at=n.created_at.isoformat(),
                    tags=list(n.tags),
                )
                for n in session.notes
            ],
            metadata=dict(session.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "technician": self.technician,
            "device": self.device.to_dict(),
            "issue": self.issue.to_dict(),
            "tests": [t.to_dict() for t in self.tests],
            "measurements": [m.to_dict() for m in self.measurements],
            "diagnoses": [d.to_dict() for d in self.diagnoses],
            "actions": [a.to_dict() for a in self.actions],
            "results": [r.to_dict() for r in self.results],
            "images": [i.to_dict() for i in self.images],
            "notes": [n.to_dict() for n in self.notes],
            "metadata": dict(self.metadata),
        }
