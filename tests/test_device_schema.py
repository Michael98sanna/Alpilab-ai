"""Tests for Device schema."""

from app.schemas.repair import Device, DeviceBrand


def test_device_defaults_and_fields() -> None:
    device = Device(brand=DeviceBrand.APPLE, model="iPhone 13", imei="123")
    assert device.id
    assert device.brand == DeviceBrand.APPLE
    assert device.model == "iPhone 13"
    assert device.imei == "123"
    assert device.metadata == {}


def test_device_serialization_roundtrip() -> None:
    device = Device(brand=DeviceBrand.SAMSUNG, model="S21", model_code="SM-G991B")
    data = device.model_dump()
    restored = Device.model_validate(data)
    assert restored.model == "S21"
    assert restored.brand == DeviceBrand.SAMSUNG
