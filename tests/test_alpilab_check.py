"""Tests for the Alpilab Check connector mock."""

from uuid import uuid4

from app.integrations.alpilab_check import (
    DeviceIdentityPayload,
    DiagnosticSnapshotPayload,
    MockAlpilabCheckConnector,
)


def test_check_connector_is_mock_and_available() -> None:
    connector = MockAlpilabCheckConnector()
    info = connector.get_info()

    assert connector.is_available() is True
    assert info.is_mock is True
    assert info.transport == "none"
    assert "check" in info.name


def test_check_connector_maps_device_identity() -> None:
    connector = MockAlpilabCheckConnector()
    device = connector.import_device_identity(
        DeviceIdentityPayload(brand="Xiaomi", model="Redmi Note 10", imei="123456789012345")
    )

    assert device.brand == "Xiaomi"
    assert device.model == "Redmi Note 10"
    assert device.imei == "123456789012345"
    assert "MockAlpilabCheckConnector" in (device.notes or "")


def test_check_connector_maps_snapshot_without_assuming_check_internals() -> None:
    connector = MockAlpilabCheckConnector()
    session_id = uuid4()
    tests = connector.import_diagnostic_snapshot(
        session_id,
        DiagnosticSnapshotPayload(
            tests=[{"name": "Wi-Fi", "result_summary": "ok"}],
            raw={"whatever_check_might_send": True},
        ),
    )

    assert len(tests) == 1
    assert tests[0].session_id == session_id
    assert tests[0].name == "Wi-Fi"
    assert tests[0].source == "alpilab_check"
    assert tests[0].raw_payload is not None
    assert tests[0].raw_payload["snapshot_raw"]["whatever_check_might_send"] is True
