"""Tests for Alpilab Check connector mock."""

from app.integrations.alpilab_check import MockAlpilabCheckConnector


def test_check_connector_mock_available():
    connector = MockAlpilabCheckConnector()
    assert connector.is_available() is True
    assert connector.name == "alpilab_check_mock"


def test_check_connector_device_snapshot():
    connector = MockAlpilabCheckConnector()
    snap = connector.fetch_device_snapshot("REF-123")
    assert snap.identifier == "REF-123"
    assert snap.raw.get("mock") is True


def test_check_connector_diagnostics():
    connector = MockAlpilabCheckConnector()
    payload = connector.fetch_diagnostics("SESS-9")
    assert payload.session_ref == "SESS-9"
    assert len(payload.tests) >= 1
    assert payload.raw.get("mock") is True
