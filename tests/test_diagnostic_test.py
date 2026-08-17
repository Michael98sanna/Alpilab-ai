"""Tests for DiagnosticTest schema."""

from datetime import datetime, timezone

from app.models import DiagnosticStatus, DiagnosticTest, SourceSystem


def test_diagnostic_test_defaults() -> None:
    test = DiagnosticTest(name="Display pixels")
    assert test.status is DiagnosticStatus.UNKNOWN
    assert test.source is SourceSystem.MANUAL
    assert test.category is None


def test_diagnostic_test_roundtrip() -> None:
    performed = datetime(2026, 8, 17, 10, 0, tzinfo=timezone.utc)
    test = DiagnosticTest(
        name="Charging port",
        category="charging",
        status=DiagnosticStatus.FAIL,
        details="Nessuna corrente in ingresso",
        source=SourceSystem.ALPILAB_CHECK,
        performed_at=performed,
    )
    restored = DiagnosticTest.model_validate(test.model_dump(mode="json"))
    assert restored.name == "Charging port"
    assert restored.status is DiagnosticStatus.FAIL
    assert restored.source is SourceSystem.ALPILAB_CHECK
    assert restored.details is not None
