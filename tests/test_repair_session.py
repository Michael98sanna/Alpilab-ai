"""Tests for RepairSession aggregate."""

from app.models.repair import (
    CustomerIssue,
    Device,
    Note,
    RepairSession,
    SessionStatus,
)
from app.schemas.repair import RepairSessionSchema
from app.services.repair_service import RepairService


def test_repair_session_creation():
    device = Device(brand="Apple", model="iPhone 12")
    issue = CustomerIssue(
        description="Non si accende",
        symptoms=["no power", "no vibration"],
    )
    session = RepairSession(device=device, issue=issue)
    assert session.status == SessionStatus.OPEN
    assert session.device.model == "iPhone 12"
    assert "no power" in session.issue.symptoms


def test_repair_session_schema_roundtrip():
    device = Device(brand="Apple", model="iPhone 12")
    issue = CustomerIssue(description="Schermo rotto")
    session = RepairSession(device=device, issue=issue, technician="lab-1")
    session.add_note(Note(content="Cliente urgente", author="lab-1"))

    schema = RepairSessionSchema.from_model(session)
    assert schema.technician == "lab-1"
    assert schema.to_dict()["device"]["model"] == "iPhone 12"
    assert len(schema.notes) == 1

    restored = schema.to_model()
    assert restored.device.brand == "Apple"
    assert restored.issue.description == "Schermo rotto"


def test_repair_service_in_memory():
    service = RepairService()
    session = service.create_session(
        Device(brand="Huawei", model="P30"),
        CustomerIssue(description="Face ID non funziona"),
        technician="mike",
    )
    assert service.get_session(session.id) is session
    assert len(service.list_sessions()) == 1
