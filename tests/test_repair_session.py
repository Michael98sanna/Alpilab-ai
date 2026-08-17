"""Tests for RepairSession as aggregate root."""

from app.models import (
    CustomerIssue,
    Device,
    Note,
    RepairSession,
    RepairSessionStatus,
)


def test_repair_session_holds_device_and_defaults(sample_device: Device) -> None:
    session = RepairSession(device=sample_device, technician="Luca")

    assert session.status is RepairSessionStatus.OPEN
    assert session.device.model == "iPhone 12"
    assert session.tests == []
    assert session.measurements == []
    assert session.diagnoses == []
    assert session.actions == []
    assert session.results == []
    assert session.images == []
    assert session.notes == []


def test_repair_session_can_attach_issue_and_note(sample_device: Device) -> None:
    session = RepairSession(device=sample_device)
    issue = CustomerIssue(
        session_id=session.id,
        description="Non si accende",
        symptoms=["no power", "no vibration"],
    )
    note = Note(session_id=session.id, content="Cliente segnala caduta.", author="banco")
    session.customer_issue = issue
    session.notes.append(note)

    dumped = session.model_dump()
    assert dumped["customer_issue"]["description"] == "Non si accende"
    assert dumped["notes"][0]["content"] == "Cliente segnala caduta."
