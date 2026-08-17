"""Tests for the Device contract."""

import pytest
from pydantic import ValidationError

from app.models import Device


def test_device_minimal_fields() -> None:
    device = Device(brand="Samsung", model="Galaxy S21")
    assert device.brand == "Samsung"
    assert device.model == "Galaxy S21"
    assert device.imei is None
    assert device.id is not None


def test_device_accepts_valid_imei() -> None:
    device = Device(brand="Apple", model="iPhone 13", imei="356938035643809")
    assert device.imei == "356938035643809"


def test_device_rejects_non_digit_imei() -> None:
    with pytest.raises(ValidationError):
        Device(brand="Apple", model="iPhone 13", imei="ABC")


def test_device_rejects_missing_brand() -> None:
    with pytest.raises(ValidationError):
        Device(brand="", model="X")
