"""Tests for Alpilab Hub mock — no real OS/hardware interaction."""

import pytest

from app.core.security import ConfirmationRequiredError
from hub.client import MockAlpilabHub


def test_hub_pc_status():
    hub = MockAlpilabHub()
    status = hub.get_pc_status()
    assert status.online is True
    assert "get_pc_status" in status.capabilities
    assert status.hub_version.endswith("mock")


def test_hub_actions_require_confirmation():
    hub = MockAlpilabHub()
    with pytest.raises(ConfirmationRequiredError):
        hub.open_application("3utools")
    with pytest.raises(ConfirmationRequiredError):
        hub.capture_microscope()
    with pytest.raises(ConfirmationRequiredError):
        hub.read_multimeter()


def test_hub_actions_with_confirmation_are_mock():
    hub = MockAlpilabHub()
    opened = hub.open_application("3utools", confirmed=True)
    assert opened.mock is True
    assert opened.success is True
    assert "nessuna app avviata" in opened.message.lower() or "MOCK" in opened.message

    capture = hub.capture_microscope(confirmed=True)
    assert capture.mock is True
    assert capture.data.get("image_path") is None

    meter = hub.read_multimeter(confirmed=True)
    assert meter.mock is True

    psu = hub.read_power_supply(confirmed=True)
    assert psu.mock is True

    closed = hub.close_application("3utools", confirmed=True)
    assert closed.mock is True

    thermal = hub.capture_thermal_camera(confirmed=True)
    assert thermal.mock is True
