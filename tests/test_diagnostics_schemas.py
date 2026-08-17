"""Tests for DiagnosticTest and Measurement schemas."""

from app.schemas import DiagnosticTest, Measurement


def test_diagnostic_test_schema():
    test = DiagnosticTest(
        name="touch_panel",
        category="display",
        result="dead zones on top edge",
        passed=False,
    )
    assert test.name == "touch_panel"
    assert test.passed is False
    assert test.id
    assert test.performed_at is not None


def test_measurement_schema():
    measurement = Measurement(
        source="multimeter",
        label="PP_BATT_VCC",
        value=3.82,
        unit="V",
        context="probe near battery connector",
    )
    assert measurement.value == 3.82
    assert measurement.unit == "V"
    dumped = measurement.model_dump()
    assert dumped["source"] == "multimeter"
