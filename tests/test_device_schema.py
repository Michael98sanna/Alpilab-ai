"""Tests for Device model and schema."""

from app.models.repair import Device, DeviceType
from app.schemas.repair import DeviceSchema


def test_device_model_defaults():
    device = Device(brand="Samsung", model="Galaxy S21")
    assert device.device_type == DeviceType.SMARTPHONE
    assert device.display_name() == "Samsung Galaxy S21"
    assert device.id


def test_device_schema_roundtrip():
    schema = DeviceSchema(
        brand="Apple",
        model="iPhone 13",
        imei="123456789012345",
        device_type=DeviceType.SMARTPHONE.value,
    )
    model = schema.to_model()
    restored = DeviceSchema.from_model(model)
    assert restored.brand == "Apple"
    assert restored.model == "iPhone 13"
    assert restored.imei == "123456789012345"
    assert restored.to_dict()["brand"] == "Apple"


def test_device_schema_from_dict():
    data = {"brand": "Xiaomi", "model": "Redmi Note 10", "color": "black"}
    schema = DeviceSchema.from_dict(data)
    assert schema.brand == "Xiaomi"
    assert schema.color == "black"
