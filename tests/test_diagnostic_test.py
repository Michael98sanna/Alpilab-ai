"""Tests for DiagnosticTest schema."""

from app.schemas.repair import DiagnosticTest, DiagnosticTestStatus


def test_diagnostic_test_defaults() -> None:
    test = DiagnosticTest(name="battery_health", category="power", source="manual")
    assert test.status == DiagnosticTestStatus.PENDING
    assert test.name == "battery_health"
    assert test.raw_data == {}


def test_diagnostic_test_completed() -> None:
    test = DiagnosticTest(
        name="touch_id",
        status=DiagnosticTestStatus.FAILED,
        result_summary="Sensore non risponde",
        source="alpilab_check",
    )
    assert test.status == DiagnosticTestStatus.FAILED
    assert "Sensore" in (test.result_summary or "")
