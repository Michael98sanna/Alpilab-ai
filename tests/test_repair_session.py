"""Tests for RepairSession and related nested models."""

from app.models import (
    CustomerIssue,
    Diagnosis,
    DiagnosticTest,
    ImageAttachment,
    ImageKind,
    Measurement,
    MeasurementKind,
    Note,
    RepairAction,
    RepairResult,
    RepairSession,
    RepairSessionStatus,
    SourceSystem,
    DiagnosticStatus,
)
from app.models.device import Device


def test_repair_session_holds_nested_contract(sample_device: Device) -> None:
    session = RepairSession(
        device=sample_device,
        technician="luca",
        customer_issue=CustomerIssue(
            summary="Non si accende",
            reported_symptoms=["schermo nero", "nessuna vibrazione"],
        ),
        diagnostic_tests=[
            DiagnosticTest(name="Power-on", status=DiagnosticStatus.FAIL),
        ],
        measurements=[
            Measurement(kind=MeasurementKind.VOLTAGE, value=0.0, unit="V", location="VBAT"),
        ],
        diagnoses=[
            Diagnosis(
                hypothesis="Corto sulla linea VBAT",
                confidence=0.4,
                facts=["Tensione VBAT a 0 V"],
                hypotheses=["Possibile corto dopo ingresso liquidi"],
                recommended_checks=["Misurare resistenza VBAT verso GND"],
            )
        ],
        actions=[RepairAction(description="Ispezionare connettore batteria")],
        results=[RepairResult(success=False, summary="Diagnosi in corso")],
        images=[ImageAttachment(filename="board.jpg", kind=ImageKind.PHOTO)],
        notes=[Note(content="Cliente segnala caduta in acqua", author="banco-1")],
    )

    assert session.status is RepairSessionStatus.OPEN
    assert session.source is SourceSystem.ALPILAB_AI
    assert session.device.model == "Galaxy S21"
    assert session.customer_issue is not None
    assert session.customer_issue.reported_symptoms == ["schermo nero", "nessuna vibrazione"]
    assert len(session.diagnostic_tests) == 1
    assert len(session.measurements) == 1
    assert session.diagnoses[0].confidence == 0.4
    assert session.images[0].kind is ImageKind.PHOTO


def test_repair_session_json_roundtrip(sample_device: Device) -> None:
    session = RepairSession(device=sample_device, status=RepairSessionStatus.IN_PROGRESS)
    payload = session.model_dump(mode="json")
    restored = RepairSession.model_validate(payload)
    assert restored.id == session.id
    assert restored.status is RepairSessionStatus.IN_PROGRESS
    assert restored.device.brand == sample_device.brand
