"""Tests for RepairSession schema."""

from app.schemas.repair import (
    CustomerIssue,
    Device,
    DeviceBrand,
    Note,
    RepairSession,
    RepairSessionStatus,
)


def test_repair_session_aggregate() -> None:
    device = Device(brand=DeviceBrand.APPLE, model="iPhone 11")
    issue = CustomerIssue(summary="Non si accende", symptoms=["no power"])
    session = RepairSession(
        device=device,
        customer_issue=issue,
        technician="lab-tech-1",
        notes=[Note(content="Cliente segnala caduta")],
    )
    assert session.status == RepairSessionStatus.OPEN
    assert session.device.model == "iPhone 11"
    assert session.customer_issue is not None
    assert session.customer_issue.summary == "Non si accende"
    assert len(session.notes) == 1
    assert session.diagnostic_tests == []
    assert session.id
