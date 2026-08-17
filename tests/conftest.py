"""Shared fixtures."""

from uuid import uuid4

import pytest

from app.models import Device


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def sample_device() -> Device:
    return Device(brand="Apple", model="iPhone 12", imei="356938035643809")
