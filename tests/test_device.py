"""Tests for Device and related domain models."""

from app.models import Device, DeviceType


def test_device_minimal():
    device = Device(brand="Apple", model="iPhone 13")
    assert device.brand == "Apple"
    assert device.model == "iPhone 13"
    assert device.device_type == DeviceType.SMARTPHONE
    assert device.id
    assert device.imei is None


def test_device_with_identifiers():
    device = Device(
        brand="Samsung",
        model="Galaxy S21",
        imei="123456789012345",
        serial_number="SN-001",
        storage_gb=128,
        device_type=DeviceType.SMARTPHONE,
    )
    assert device.imei == "123456789012345"
    assert device.storage_gb == 128
    payload = device.model_dump()
    assert payload["brand"] == "Samsung"
    assert payload["device_type"] == "smartphone"
