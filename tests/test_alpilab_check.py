"""Tests for AlpilabCheckConnector mock."""

from app.integrations import MockAlpilabCheckConnector
from app.models import (
    CustomerIssue,
    Device,
    DiagnosticTest,
    RepairSession,
    DiagnosticResultStatus,
)


def test_check_connector_mock_available():
    connector = MockAlpilabCheckConnector()
    assert connector.is_available() is True
    assert connector.ping()["available"] is True
    assert "mock" in connector.name


def test_check_connector_device_roundtrip():
    connector = MockAlpilabCheckConnector()
    device = Device(brand="Apple", model="iPhone 12", imei="111")
    connector.register_device("ext-1", device)
    loaded = connector.get_device("ext-1")
    assert loaded is not None
    assert loaded.imei == "111"
    assert connector.get_device("missing") is None


def test_check_connector_tests_and_session():
    connector = MockAlpilabCheckConnector()
    tests = [
        DiagnosticTest(name="WiFi", status=DiagnosticResultStatus.PASS),
        DiagnosticTest(name="Bluetooth", status=DiagnosticResultStatus.FAIL),
    ]
    connector.register_tests("job-9", tests)
    assert len(connector.list_diagnostic_tests("job-9")) == 2

    session = RepairSession(
        device=Device(brand="OnePlus", model="9"),
        customer_issue=CustomerIssue(summary="No signal"),
    )
    connector.register_session("job-9", session)
    imported = connector.import_repair_session("job-9")
    assert imported is not None
    assert imported.device.brand == "OnePlus"
    assert connector.export_notes("job-9", ["nota mock"]) is True
