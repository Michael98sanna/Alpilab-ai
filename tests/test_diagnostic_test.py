"""Tests for DiagnosticTest model and schema."""

from datetime import datetime, timezone

from app.models.repair import DiagnosticStatus, DiagnosticTest
from app.schemas.repair import DiagnosticTestSchema


def test_diagnostic_test_defaults():
    test = DiagnosticTest(name="Diode mode on backlight line")
    assert test.status == DiagnosticStatus.PENDING
    assert test.id


def test_diagnostic_test_schema_roundtrip():
    now = datetime.now(timezone.utc)
    test = DiagnosticTest(
        name="USB charging test",
        status=DiagnosticStatus.PASSED,
        procedure="Apply 5V and measure current draw",
        expected_result="~500mA idle",
        actual_result="480mA",
        performed_at=now,
    )
    schema = DiagnosticTestSchema.from_model(test)
    restored = schema.to_model()
    assert restored.name == "USB charging test"
    assert restored.status == DiagnosticStatus.PASSED
    assert restored.actual_result == "480mA"
    assert schema.to_dict()["status"] == "passed"
