"""Tests for Alpilab Check connector mock."""

from app.integrations import MockAlpilabCheckConnector


def test_check_connector_mock_available():
    connector = MockAlpilabCheckConnector()
    assert connector.is_available() is True
    snapshot = connector.get_connected_device()
    assert snapshot is not None
    assert snapshot.device.brand == "Apple"
    assert snapshot.source == "alpilab_check_mock"


def test_check_connector_mock_diagnostics():
    connector = MockAlpilabCheckConnector()
    diagnostics = connector.get_diagnostics()
    assert diagnostics is not None
    assert len(diagnostics.tests) == 1
    assert diagnostics.tests[0].name == "battery_health"
    assert diagnostics.measurements[0].unit == "cycles"


def test_check_connector_mock_unavailable():
    connector = MockAlpilabCheckConnector(available=False)
    assert connector.is_available() is False
    assert connector.get_connected_device() is None
    assert connector.get_diagnostics() is None
    assert connector.push_session_reference("sess-1") is False


def test_check_connector_push_session():
    connector = MockAlpilabCheckConnector()
    assert connector.push_session_reference("sess-abc") is True
    assert connector._pushed_sessions == ["sess-abc"]
