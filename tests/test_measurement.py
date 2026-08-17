"""Tests for Measurement model."""

from app.models.repair import Measurement


def test_measurement_basic():
    m = Measurement(name="PP_BATT_VCC", value="3.82", unit="V", instrument="multimeter")
    assert m.name == "PP_BATT_VCC"
    assert m.value == "3.82"
    assert m.unit == "V"
    assert m.recorded_at is not None


def test_measurement_textual_value():
    m = Measurement(name="thermal_hotspot", value="punto caldo near CPU", instrument="thermal_camera")
    assert "CPU" in m.value
    assert m.unit is None
