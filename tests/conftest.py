"""Shared test fixtures."""

from __future__ import annotations

import pytest

from app.models import Device, DeviceIdentifierType


@pytest.fixture
def sample_device() -> Device:
    return Device(
        brand="Samsung",
        model="Galaxy S21",
        identifier="351234567890123",
        identifier_type=DeviceIdentifierType.IMEI,
        os_name="Android",
        os_version="13",
        storage_gb=128,
    )
