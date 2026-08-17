"""Tests for Alpilab Check connector mock."""

from app.integrations.alpilab_check_mock import MockAlpilabCheckConnector


def test_check_connector_connected() -> None:
    connector = MockAlpilabCheckConnector(connected=True)
    assert connector.is_connected() is True
    device = connector.get_device_info("SN123")
    assert device is not None
    assert device.brand == "MockBrand"
    assert device.serial_number == "SN123"


def test_check_connector_diagnostic_snapshot() -> None:
    connector = MockAlpilabCheckConnector()
    snapshot = connector.get_diagnostic_snapshot("session-abc")
    assert snapshot is not None
    assert snapshot.session_reference == "session-abc"
    assert len(snapshot.tests) == 1


def test_check_connector_push_update() -> None:
    connector = MockAlpilabCheckConnector()
    assert connector.push_repair_update({"status": "in_progress"}) is True


def test_check_connector_disconnected() -> None:
    connector = MockAlpilabCheckConnector(connected=False)
    assert connector.is_connected() is False
    assert connector.get_device_info("SN123") is None
