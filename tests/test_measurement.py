"""Tests for Measurement model."""

from app.models import Measurement, MeasurementUnit


def test_measurement_voltage():
    m = Measurement(
        name="PP_VCC_MAIN",
        value=3.72,
        unit=MeasurementUnit.VOLT,
        probe_point="C1201",
        source="multimeter",
    )
    assert m.value == 3.72
    assert m.unit == MeasurementUnit.VOLT
    assert m.probe_point == "C1201"
    assert m.model_dump()["unit"] == "V"


def test_measurement_other_unit():
    m = Measurement(name="temperatura hotspot", value=68.5, unit=MeasurementUnit.CELSIUS)
    assert m.unit == MeasurementUnit.CELSIUS
    assert m.id
