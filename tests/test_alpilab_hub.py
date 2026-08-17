"""Tests for AlpilabHub mock — no real process or hardware access."""

from hub import MockAlpilabHub


def test_hub_mock_status():
    hub = MockAlpilabHub()
    assert hub.is_available() is True
    status = hub.get_pc_status()
    assert status.online is True
    assert status.details.get("mock") is True


def test_hub_open_requires_confirmation():
    hub = MockAlpilabHub()
    result = hub.open_application("3utools", confirmed=False)
    assert result.success is False
    assert result.requires_confirmation is True
    assert result.mock is True
    assert "MOCK" in result.message


def test_hub_open_with_confirmation_still_mock():
    hub = MockAlpilabHub()
    result = hub.open_application("3utools", confirmed=True)
    assert result.success is True
    assert result.confirmed is True
    assert "nessun processo" in result.message.lower() or "MOCK" in result.message


def test_hub_unknown_app_rejected():
    hub = MockAlpilabHub()
    result = hub.open_application("cmd.exe", confirmed=True)
    assert result.success is False
    assert "allow-list" in result.message.lower() or "allow-list" in result.message


def test_hub_capture_and_read_placeholders():
    hub = MockAlpilabHub()
    assert hub.capture_microscope().action == "capture_microscope"
    assert hub.capture_thermal_camera().success is True
    assert hub.read_multimeter().data["value"] is None
    assert hub.read_power_supply().action == "read_power_supply"
    assert hub.close_application("alpilab_check", confirmed=True).success is True
