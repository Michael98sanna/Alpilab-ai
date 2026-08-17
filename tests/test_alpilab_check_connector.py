"""Tests for Alpilab Check connector mock."""

from app.integrations.alpilab_check import MockAlpilabCheckConnector


def test_check_connector_mock_available() -> None:
    connector = MockAlpilabCheckConnector()
    assert connector.ping() is True
    assert connector.is_available() is True
    device = connector.get_connected_device()
    assert device is not None
    assert device.model == "iPhone 13"
    assert device.raw.get("source") == "mock"


def test_check_connector_mock_diagnostics() -> None:
    connector = MockAlpilabCheckConnector()
    results = connector.get_latest_diagnostics()
    assert len(results) == 1
    assert results[0].test_name == "battery_health"


def test_check_connector_unavailable() -> None:
    connector = MockAlpilabCheckConnector(available=False)
    assert connector.ping() is False
    assert connector.get_connected_device() is None
    assert connector.get_latest_diagnostics() == []
