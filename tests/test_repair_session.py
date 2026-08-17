"""Tests for RepairSession aggregate."""

from app.models import (
    CustomerIssue,
    Device,
    DeviceBrand,
    RepairSession,
    RepairSessionStatus,
)


def test_repair_session_minimal():
    session = RepairSession(
        device=Device(brand=DeviceBrand.APPLE, model="iPhone 11"),
        customer_issue=CustomerIssue(description="Non si accende"),
    )
    assert session.status == RepairSessionStatus.INTAKE
    assert session.customer_issue is not None
    assert session.customer_issue.description == "Non si accende"
    assert session.diagnostic_tests == []
    assert session.result is None


def test_repair_session_with_external_ref():
    session = RepairSession(
        device=Device(brand=DeviceBrand.OTHER, model="Unknown"),
        external_refs={"alpilab_check_id": "chk-42"},
    )
    assert session.external_refs["alpilab_check_id"] == "chk-42"
