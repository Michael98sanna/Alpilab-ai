"""Tests for Measurement model and schema."""

from app.models.repair import Measurement
from app.schemas.repair import MeasurementSchema


def test_measurement_model():
    m = Measurement(
        name="PP_BATT_VCC",
        value="3.82",
        unit="V",
        source="multimeter",
        notes="Measured at coil L1202",
    )
    assert m.value == "3.82"
    assert m.unit == "V"
    assert m.source == "multimeter"


def test_measurement_schema_roundtrip():
    schema = MeasurementSchema(
        name="current_draw",
        value="0.12",
        unit="A",
        source="power_supply",
    )
    model = schema.to_model()
    restored = MeasurementSchema.from_model(model)
    assert restored.name == "current_draw"
    assert restored.value == "0.12"
    assert restored.unit == "A"
    assert restored.to_dict()["source"] == "power_supply"
