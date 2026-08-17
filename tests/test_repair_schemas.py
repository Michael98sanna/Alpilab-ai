"""Tests for Device and RepairSession schemas."""

from app.schemas import (
    CustomerIssue,
    Device,
    RepairSession,
    RepairStatus,
)


def test_device_schema_minimal():
    device = Device(brand="Samsung", model="Galaxy S21")
    assert device.brand == "Samsung"
    assert device.model == "Galaxy S21"
    assert device.id
    assert device.metadata == {}


def test_device_schema_with_identifiers():
    device = Device(
        brand="Apple",
        model="iPhone 13",
        model_code="A2633",
        imei="356938035643809",
        serial_number="C7XYZ123",
    )
    assert device.imei.startswith("3569")
    payload = device.model_dump()
    assert payload["model_code"] == "A2633"


def test_repair_session_aggregate():
    session = RepairSession(
        device=Device(brand="Xiaomi", model="Redmi Note 11"),
        customer_issue=CustomerIssue(
            summary="Non carica",
            symptoms=["no charge", "hot connector"],
        ),
        technician="lab-tech-1",
    )
    assert session.status == RepairStatus.OPEN
    assert session.customer_issue.summary == "Non carica"
    assert session.diagnostic_tests == []
    assert session.external_refs == {}
    assert session.id
