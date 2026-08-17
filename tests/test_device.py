"""Tests for the Device schema (shared contract)."""

from app.models import Device, DeviceIdentifierType


def test_device_requires_brand_and_model() -> None:
    device = Device(brand="Xiaomi", model="Redmi Note 10")
    assert device.brand == "Xiaomi"
    assert device.model == "Redmi Note 10"
    assert device.identifier is None
    assert device.identifier_type is DeviceIdentifierType.UNKNOWN


def test_device_json_roundtrip(sample_device: Device) -> None:
    payload = sample_device.model_dump(mode="json")
    restored = Device.model_validate(payload)
    assert restored.id == sample_device.id
    assert restored.identifier == "351234567890123"
    assert restored.identifier_type is DeviceIdentifierType.IMEI
    assert restored.storage_gb == 128


def test_device_identifier_types() -> None:
    serial = Device(
        brand="Apple",
        model="iPhone 11",
        identifier="F2LX1234",
        identifier_type=DeviceIdentifierType.SERIAL,
    )
    assert serial.identifier_type.value == "serial"
