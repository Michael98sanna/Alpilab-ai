"""Tests for Measurement schema."""

from app.models import Measurement, MeasurementKind, SourceSystem


def test_measurement_voltage() -> None:
    reading = Measurement(
        kind=MeasurementKind.VOLTAGE,
        value=3.82,
        unit="V",
        location="PP_BATT",
        source=SourceSystem.ALPILAB_HUB,
        instrument="multimeter",
    )
    assert reading.kind is MeasurementKind.VOLTAGE
    assert reading.value == 3.82
    assert reading.unit == "V"
    assert reading.taken_at.tzinfo is not None


def test_measurement_roundtrip() -> None:
    reading = Measurement(kind=MeasurementKind.TEMPERATURE, value=41.5, unit="C", location="PMIC")
    restored = Measurement.model_validate(reading.model_dump(mode="json"))
    assert restored.kind is MeasurementKind.TEMPERATURE
    assert restored.value == 41.5
    assert restored.location == "PMIC"
