"""Tests for Device schema/model."""

from app.models.device import Device


def test_device_requires_brand_and_model():
    device = Device(brand="Apple", model="iPhone 12")
    assert device.brand == "Apple"
    assert device.model == "iPhone 12"
    assert device.id
    assert device.created_at is not None


def test_device_optional_fields():
    device = Device(
        brand="Samsung",
        model="Galaxy S21",
        identifier="356789012345678",
        color="nero",
        storage_gb=128,
        os_version="Android 13",
    )
    assert device.identifier.startswith("356")
    assert device.storage_gb == 128


def test_device_serialization_roundtrip():
    device = Device(brand="Xiaomi", model="Redmi Note 10")
    data = device.model_dump()
    restored = Device.model_validate(data)
    assert restored.id == device.id
    assert restored.model == "Redmi Note 10"
