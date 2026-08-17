"""Tests for Device domain schema."""

from app.models import Device, DeviceBrand


def test_device_defaults_and_fields():
    device = Device(brand=DeviceBrand.APPLE, model="iPhone 13")
    assert device.id
    assert device.brand == DeviceBrand.APPLE
    assert device.model == "iPhone 13"
    assert device.imei is None
    assert device.created_at is not None


def test_device_serialization_roundtrip():
    device = Device(
        brand=DeviceBrand.SAMSUNG,
        model="Galaxy S21",
        model_code="SM-G991B",
        imei="123456789012345",
    )
    data = device.model_dump()
    restored = Device.model_validate(data)
    assert restored.model == "Galaxy S21"
    assert restored.model_code == "SM-G991B"
    assert restored.imei == "123456789012345"
