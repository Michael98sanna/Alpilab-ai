"""Tests for Measurement schema."""

from app.models import Measurement


def test_measurement_numeric():
    m = Measurement(
        name="PP_VCC_MAIN",
        value=3.82,
        unit="V",
        probe_point="C1520",
        instrument="multimeter",
    )
    assert m.value == 3.82
    assert m.unit == "V"
    assert m.instrument == "multimeter"


def test_measurement_string_value():
    m = Measurement(name="continuity", value="open", unit=None)
    assert m.value == "open"
