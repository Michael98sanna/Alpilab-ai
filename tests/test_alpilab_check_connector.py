"""Tests for Alpilab Check connector mock."""

from app.integrations import MockAlpilabCheckConnector


def test_check_connector_mock_device():
    connector = MockAlpilabCheckConnector()
    assert connector.is_available() is True
    device = connector.fetch_device("demo-1")
    assert device is not None
    assert device.model == "iPhone 12"
    assert connector.fetch_device("missing") is None


def test_check_connector_mock_diagnostics_and_push():
    connector = MockAlpilabCheckConnector()
    payload = connector.fetch_diagnostics("session-demo")
    assert payload is not None
    assert len(payload.tests) >= 1
    assert connector.push_repair_summary("session-demo", {"ok": True}) is True
