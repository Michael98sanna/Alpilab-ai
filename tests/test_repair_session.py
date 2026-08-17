"""Tests for RepairSession and related models."""

from app.models.device import Device
from app.models.repair import (
    CustomerIssue,
    Diagnosis,
    DiagnosticTest,
    ImageAttachment,
    Measurement,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
    SessionStatus,
    DiagnosticTestStatus,
)
from app.services.repair_service import RepairService


def test_repair_session_aggregate():
    issue = CustomerIssue(
        description="Non carica",
        symptoms=["no charge", "hot cable"],
    )
    session = RepairSession(
        device_id="dev-1",
        customer_issue=issue,
        diagnostic_tests=[
            DiagnosticTest(name="USB continuity", status=DiagnosticTestStatus.PENDING),
        ],
        measurements=[
            Measurement(name="VBUS", value="0.02", unit="V", instrument="multimeter"),
        ],
        diagnoses=[
            Diagnosis(summary="Possibile U2 charging IC", confidence="medium"),
        ],
        actions=[RepairAction(description="Ispezionare connettore Lightning")],
        images=[
            ImageAttachment(
                filename="port.jpg",
                path="/storage/port.jpg",
                kind="photo",
            )
        ],
        notes=[Note(content="Cliente segnala caduta recente")],
    )
    assert session.status == SessionStatus.INTAKE
    assert session.customer_issue is not None
    assert len(session.diagnostic_tests) == 1
    assert session.measurements[0].unit == "V"
    assert session.result is None


def test_repair_result_on_session():
    session = RepairSession(device_id="dev-2")
    session.result = RepairResult(
        success=True,
        summary="Sostituito connettore di carica",
        verified_tests=["charge_test"],
    )
    assert session.result.success is True


def test_repair_service_open_session():
    service = RepairService()
    device = service.create_device(Device(brand="Apple", model="iPhone 11"))
    session = service.open_session(device.id, technician="lab-1")
    assert session.device_id == device.id
    assert service.get_session(session.id) is not None
    assert len(service.list_sessions()) == 1
