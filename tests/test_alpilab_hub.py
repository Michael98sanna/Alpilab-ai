"""Tests for Alpilab Hub mock."""

from hub import MockAlpilabHub


def test_hub_pc_status():
    hub = MockAlpilabHub()
    status = hub.get_pc_status()
    assert status.online is True
    assert "capture_microscope" in status.capabilities
    assert status.metadata.get("mock") is True


def test_hub_requires_confirmation_for_open_app():
    hub = MockAlpilabHub()
    denied = hub.open_application("3utools")
    assert denied.ok is False
    assert denied.requires_confirmation is True
    assert "No OS command was executed" in denied.message

    allowed = hub.open_application("3utools", confirmed=True)
    assert allowed.ok is True
    assert allowed.mock is True
    assert allowed.data["app_id"] == "3utools"


def test_hub_hardware_mocks_do_not_touch_os():
    hub = MockAlpilabHub()
    assert hub.capture_microscope().mock is True
    assert hub.capture_thermal_camera().mock is True
    assert hub.read_multimeter().data["value"] is None
    assert hub.read_power_supply().action == "read_power_supply"
