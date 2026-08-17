"""Tests for Alpilab Hub mock."""

from hub import MockAlpilabHub


def test_hub_status_and_reads():
    hub = MockAlpilabHub()
    assert hub.is_available() is True
    status = hub.get_pc_status()
    assert status.online is True
    assert "read_multimeter" in status.capabilities

    meter = hub.read_multimeter()
    assert meter.is_mock is True
    assert meter.success is True

    psu = hub.read_power_supply()
    assert psu.is_mock is True

    micro = hub.capture_microscope()
    assert micro.source == "microscope"
    assert micro.is_mock is True

    thermal = hub.capture_thermal_camera()
    assert thermal.source == "thermal_camera"


def test_hub_open_requires_confirmation():
    hub = MockAlpilabHub(granted_permissions={"*"})
    denied = hub.open_application("3utools", confirmed=False)
    assert denied.success is False
    assert denied.requires_confirmation is True

    allowed = hub.open_application("3utools", confirmed=True)
    assert allowed.success is True
    assert "[MOCK]" in allowed.message


def test_hub_no_permission():
    hub = MockAlpilabHub(granted_permissions=set())
    result = hub.close_application("borneo", confirmed=True)
    assert result.success is False
