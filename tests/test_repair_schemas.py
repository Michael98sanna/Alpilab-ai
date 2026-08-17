"""Tests for repair domain schemas."""

from datetime import datetime

from app.schemas.enums import (
    DiagnosisConfidence,
    DiagnosticTestStatus,
    ImageAttachmentKind,
    RepairSessionStatus,
)
from app.schemas.repair import (
    CustomerIssue,
    Device,
    Diagnosis,
    DiagnosticTest,
    ImageAttachment,
    Measurement,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
)


def test_device_schema() -> None:
    device = Device(
        id="dev-1",
        brand="Apple",
        model="iPhone 12",
        imei="123456789012345",
    )
    assert device.brand == "Apple"
    assert device.model == "iPhone 12"


def test_repair_session_schema() -> None:
    session = RepairSession(
        id="session-1",
        device_id="dev-1",
        status=RepairSessionStatus.IN_PROGRESS,
        opened_at=datetime(2026, 1, 1, 10, 0, 0),
    )
    assert session.status == RepairSessionStatus.IN_PROGRESS
    assert session.device_id == "dev-1"


def test_customer_issue_schema() -> None:
    issue = CustomerIssue(
        id="issue-1",
        repair_session_id="session-1",
        description="Non si accende",
        symptoms=["no_power", "no_vibration"],
    )
    assert "no_power" in issue.symptoms


def test_diagnostic_test_schema() -> None:
    test = DiagnosticTest(
        id="test-1",
        repair_session_id="session-1",
        name="Test tensione batteria",
        status=DiagnosticTestStatus.PASSED,
        actual_result="3.9V",
    )
    assert test.status == DiagnosticTestStatus.PASSED


def test_measurement_schema() -> None:
    measurement = Measurement(
        id="meas-1",
        repair_session_id="session-1",
        source="multimeter",
        label="battery_voltage",
        value=3.82,
        unit="V",
    )
    assert measurement.value == 3.82
    assert measurement.unit == "V"


def test_diagnosis_schema() -> None:
    diagnosis = Diagnosis(
        id="diag-1",
        repair_session_id="session-1",
        summary="Possibile fault PMIC",
        confidence=DiagnosisConfidence.MEDIUM,
    )
    assert diagnosis.confidence == DiagnosisConfidence.MEDIUM


def test_repair_action_and_result_schemas() -> None:
    action = RepairAction(
        id="action-1",
        repair_session_id="session-1",
        description="Sostituzione connettore",
        requires_confirmation=True,
    )
    result = RepairResult(
        id="result-1",
        repair_session_id="session-1",
        summary="Riparazione completata",
    )
    assert action.requires_confirmation is True
    assert result.repair_session_id == "session-1"


def test_image_attachment_and_note_schemas() -> None:
    image = ImageAttachment(
        id="img-1",
        repair_session_id="session-1",
        kind=ImageAttachmentKind.MICROSCOPE,
        storage_reference="storage/session-1/microscope.jpg",
    )
    note = Note(
        id="note-1",
        repair_session_id="session-1",
        content="Connettore ossidato",
        author="tech-1",
    )
    assert image.kind == ImageAttachmentKind.MICROSCOPE
    assert note.content == "Connettore ossidato"
