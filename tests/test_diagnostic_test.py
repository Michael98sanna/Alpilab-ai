"""Tests for DiagnosticTest schema."""

from app.models import DiagnosticTest


def test_diagnostic_test_fields():
    test = DiagnosticTest(
        name="battery_health",
        category="battery",
        result="86%",
        passed=True,
        source="manual",
        raw_data={"cycle_count": 412},
    )
    assert test.name == "battery_health"
    assert test.passed is True
    assert test.raw_data["cycle_count"] == 412
    assert test.id
    assert test.performed_at is not None
