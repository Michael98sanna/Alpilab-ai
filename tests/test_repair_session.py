"""Tests for RepairSession aggregate."""

from app.models import (
    CustomerIssue,
    Device,
    Diagnosis,
    Note,
    RepairSession,
    RepairStatus,
)


def test_repair_session_create():
    device = Device(brand="Xiaomi", model="Redmi Note 11")
    issue = CustomerIssue(
        summary="Non carica",
        symptoms=["led assente", "cavo ok"],
    )
    session = RepairSession(
        device=device,
        customer_issue=issue,
        technician="lab-1",
    )
    assert session.status == RepairStatus.OPEN
    assert session.device.model == "Redmi Note 11"
    assert session.customer_issue is not None
    assert "Non carica" == session.customer_issue.summary
    assert session.diagnostic_tests == []
    assert session.result is None


def test_repair_session_with_diagnosis_and_notes():
    session = RepairSession(
        device=Device(brand="Apple", model="iPhone 11"),
        diagnoses=[
            Diagnosis(
                summary="Possibile IC carica",
                confidence=0.6,
                hypotheses=["U2 faulty", "traccia interrotta"],
                created_by="ai",
            )
        ],
        notes=[Note(content="Cliente segnala caduta", author="desk")],
        external_refs={"alpilab_check_job_id": "CHK-42"},
    )
    assert len(session.diagnoses) == 1
    assert session.diagnoses[0].confidence == 0.6
    assert session.notes[0].author == "desk"
    assert session.external_refs["alpilab_check_job_id"] == "CHK-42"
    assert session.model_dump()["status"] == "open"
