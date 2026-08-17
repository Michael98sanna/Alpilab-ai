"""Tests for Alpilab Hub mock."""

from hub.mock import MockAlpilabHub


def test_hub_mock_status():
    hub = MockAlpilabHub()
    assert hub.is_available() is True
    status = hub.get_pc_status()
    assert status.online is True
    assert status.hostname == "mock-lab-pc"
    assert "get_pc_status" in status.capabilities
    assert status.metadata.get("mock") is True


def test_hub_mock_blocks_dangerous_actions_by_default():
    hub = MockAlpilabHub()
    result = hub.open_application("3utools", confirmed=False)
    assert result.success is False
    assert result.is_mock is True
    assert result.requires_confirmation is True
    assert "bloccata" in result.message.lower() or "MOCK" in result.message


def test_hub_mock_hardware_reads_are_mock():
    hub = MockAlpilabHub()
    # Even if policy later allows, mock must never claim real hardware data.
    for method in (
        hub.capture_microscope,
        hub.capture_thermal_camera,
        hub.read_multimeter,
        hub.read_power_supply,
    ):
        result = method(confirmed=True)
        assert result.is_mock is True
        # Default policy disables dangerous actions entirely.
        assert result.success is False


def test_hub_unavailable():
    hub = MockAlpilabHub(available=False)
    assert hub.is_available() is False
    result = hub.read_multimeter(confirmed=True)
    assert result.success is False
    assert "non disponibile" in result.message.lower()
