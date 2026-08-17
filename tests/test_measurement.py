"""Tests for Measurement schema."""

from app.schemas.repair import Measurement, MeasurementUnit


def test_measurement_fields() -> None:
    m = Measurement(
        label="PP_BATT_VCC",
        value=3.82,
        unit=MeasurementUnit.VOLT,
        probe_point="C1201",
        instrument="multimeter",
    )
    assert m.value == 3.82
    assert m.unit == MeasurementUnit.VOLT
    assert m.instrument == "multimeter"
    assert m.recorded_at is not None
