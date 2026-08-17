"""Tests for Measurement."""

from app.models import Measurement, MeasurementSource


def test_measurement_records_voltage(session_id) -> None:
    measurement = Measurement(
        session_id=session_id,
        name="PP_VCC_MAIN",
        source=MeasurementSource.MULTIMETER,
        value=3.72,
        unit="V",
        probe_point="PP_VCC_MAIN",
        expected_min=3.6,
        expected_max=4.2,
        in_range=True,
    )

    assert measurement.value == 3.72
    assert measurement.unit == "V"
    assert measurement.in_range is True
    assert measurement.source is MeasurementSource.MULTIMETER


def test_measurement_allows_unknown_value(session_id) -> None:
    measurement = Measurement(
        session_id=session_id,
        name="consumo idle",
        source=MeasurementSource.POWER_SUPPLY,
    )
    assert measurement.value is None
    assert measurement.in_range is None
