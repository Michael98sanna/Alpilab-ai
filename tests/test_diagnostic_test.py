"""Tests for DiagnosticTest model."""

from datetime import datetime, timezone

from app.models import DiagnosticResultStatus, DiagnosticTest


def test_diagnostic_test_defaults():
    test = DiagnosticTest(name="Touch screen")
    assert test.status == DiagnosticResultStatus.NOT_RUN
    assert test.performed_at is None
    assert test.id


def test_diagnostic_test_completed():
    now = datetime.now(timezone.utc)
    test = DiagnosticTest(
        name="Face ID",
        status=DiagnosticResultStatus.FAIL,
        performed_at=now,
        details="Errore calibratura",
        source="manual",
    )
    assert test.status == DiagnosticResultStatus.FAIL
    assert test.source == "manual"
    assert test.model_dump()["status"] == "fail"
