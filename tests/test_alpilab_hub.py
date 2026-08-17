"""Tests for Alpilab Hub mock."""

from hub.alpilab_hub import HubCapability
from hub.mock_hub import MockAlpilabHub


def test_hub_is_available() -> None:
    hub = MockAlpilabHub()
    assert hub.is_available() is True
    assert HubCapability.CAPTURE_MICROSCOPE in hub.capabilities()


def test_hub_open_and_close_application() -> None:
    hub = MockAlpilabHub()
    open_result = hub.open_application("3uTools")
    close_result = hub.close_application("3uTools")
    assert open_result.success is True
    assert close_result.success is True
    assert open_result.requires_confirmation is True


def test_hub_capture_devices() -> None:
    hub = MockAlpilabHub()
    microscope = hub.capture_microscope()
    thermal = hub.capture_thermal_camera()
    assert microscope.success is True
    assert thermal.success is True
    assert "mock/microscope.jpg" in microscope.data["storage_reference"]


def test_hub_read_measurements() -> None:
    hub = MockAlpilabHub()
    multimeter = hub.read_multimeter()
    supply = hub.read_power_supply()
    assert multimeter.data["unit"] == "V"
    assert supply.data["output_enabled"] is True


def test_hub_pc_status() -> None:
    hub = MockAlpilabHub()
    status = hub.get_pc_status()
    assert status.online is True
    assert status.hostname == "mock-pc"


def test_hub_unavailable() -> None:
    hub = MockAlpilabHub(available=False)
    assert hub.is_available() is False
    result = hub.open_application("ZXW")
    assert result.success is False
