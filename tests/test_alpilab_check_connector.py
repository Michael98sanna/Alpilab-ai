"""Tests for Alpilab Check connector mock."""

from app.integrations.alpilab_check import MockAlpilabCheckConnector


def test_check_connector_mock_available():
    connector = MockAlpilabCheckConnector()
    assert connector.is_available() is True
    assert connector.ping() is True
    assert connector.name == "alpilab_check_mock"


def test_check_connector_mock_snapshots():
    connector = MockAlpilabCheckConnector()
    device = connector.get_device_snapshot()
    diagnostic = connector.get_diagnostic_snapshot()
    assert device is not None
    assert device.brand == "Apple"
    assert device.raw.get("mock") is True
    assert diagnostic is not None
    assert "[MOCK]" in (diagnostic.summary or "")


def test_check_connector_unavailable():
    connector = MockAlpilabCheckConnector(available=False)
    assert connector.is_available() is False
    assert connector.get_device_snapshot() is None
    assert connector.get_diagnostic_snapshot() is None
    assert connector.ping() is False
