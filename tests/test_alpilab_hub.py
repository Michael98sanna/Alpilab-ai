"""Tests for Alpilab Hub mock."""

from hub import MockAlpilabHub, HubPermission


def test_hub_mock_pc_status() -> None:
    hub = MockAlpilabHub()
    assert hub.is_available() is True
    status = hub.get_pc_status()
    assert status.online is True
    assert status.hostname == "mock-lab-pc"
    assert status.metadata.get("is_mock") is True


def test_hub_dangerous_action_requires_confirmation() -> None:
    hub = MockAlpilabHub()
    blocked = hub.open_application("3uTools", confirmed=False)
    assert blocked.success is False
    assert blocked.requires_confirmation is True
    assert blocked.action == HubPermission.OPEN_APPLICATION

    allowed = hub.open_application("3uTools", confirmed=True)
    assert allowed.success is True
    assert "MOCK" in allowed.message
    assert "Nessun processo avviato" in allowed.message


def test_hub_instrument_mocks() -> None:
    hub = MockAlpilabHub()
    assert hub.capture_microscope().is_mock is True
    assert hub.capture_thermal_camera().success is True
    meter = hub.read_multimeter()
    assert meter.data.get("unit") == "V"
    psu = hub.read_power_supply()
    assert "voltage" in psu.data
