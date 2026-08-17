"""Tests for the Alpilab Check connector mock."""

from app.integrations.alpilab_check import MockAlpilabCheckConnector
from app.models import SourceSystem


def test_mock_check_connector_is_available() -> None:
    connector = MockAlpilabCheckConnector()
    assert connector.name == "mock_alpilab_check"
    assert connector.is_available() is True


def test_mock_check_connector_returns_sample_device() -> None:
    connector = MockAlpilabCheckConnector()
    device = connector.fetch_device("000000000000000")
    assert device is not None
    assert device.brand == "Apple"
    assert device.model == "iPhone 12"
    assert "MOCK" in (device.notes or "")


def test_mock_check_connector_unknown_device() -> None:
    connector = MockAlpilabCheckConnector()
    assert connector.fetch_device("unknown") is None


def test_mock_check_connector_session_snapshot() -> None:
    connector = MockAlpilabCheckConnector()
    snapshot = connector.fetch_session_snapshot(connector.sample_session_id)
    assert snapshot is not None
    assert snapshot.source is SourceSystem.ALPILAB_CHECK
    tests = connector.fetch_diagnostic_tests(connector.sample_session_id)
    assert len(tests) == 1
    assert tests[0].source is SourceSystem.ALPILAB_CHECK


def test_mock_check_connector_unknown_session() -> None:
    connector = MockAlpilabCheckConnector()
    assert connector.fetch_session_snapshot(connector.unused_uuid()) is None
    assert connector.fetch_diagnostic_tests("missing") == []
