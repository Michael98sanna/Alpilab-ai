"""Tests for the Alpilab Hub mock. No OS commands are executed."""

import hub.mock as hub_mock_module
from app.core.security import ConfirmationRequired, PermissionContext, PermissionDenied
from hub import MockAlpilabHub, full_lab_permissions
from hub.base import KnownApplication
from hub.permissions import CLOSE_APPLICATION, GET_PC_STATUS, OPEN_APPLICATION


def test_mock_hub_is_available() -> None:
    hub = MockAlpilabHub()
    assert hub.name == "mock_alpilab_hub"
    assert hub.is_available() is True


def test_mock_hub_does_not_import_subprocess() -> None:
    assert "subprocess" not in dir(hub_mock_module)
    assert "os.system" not in hub_mock_module.__dict__


def test_mock_hub_pc_status_requires_permission() -> None:
    hub = MockAlpilabHub()
    denied = PermissionContext(actor="guest", allowed_actions=frozenset())
    try:
        hub.get_pc_status(denied)
    except PermissionDenied:
        pass
    else:
        raise AssertionError("Expected PermissionDenied")

    result = hub.get_pc_status(full_lab_permissions())
    assert result.is_mock is True
    assert result.ok is True
    assert result.action == GET_PC_STATUS
    assert "[MOCK HUB]" in result.message


def test_mock_hub_open_application_is_mock_only() -> None:
    hub = MockAlpilabHub()
    result = hub.open_application(KnownApplication.THREE_UTOOLS, full_lab_permissions())
    assert result.action == OPEN_APPLICATION
    assert result.is_mock is True
    assert "No process started" in result.message
    assert result.data["application"] == "3utools"


def test_mock_hub_close_application_requires_confirmation() -> None:
    hub = MockAlpilabHub()
    permission = full_lab_permissions()
    try:
        hub.close_application(KnownApplication.ALPILAB_CHECK, permission, confirmed=False)
    except ConfirmationRequired:
        pass
    else:
        raise AssertionError("Expected ConfirmationRequired")

    result = hub.close_application(
        KnownApplication.ALPILAB_CHECK,
        permission,
        confirmed=True,
    )
    assert result.action == CLOSE_APPLICATION
    assert result.is_mock is True
    assert result.data["confirmed"] is True


def test_mock_hub_hardware_reads_are_placeholders() -> None:
    hub = MockAlpilabHub()
    permission = full_lab_permissions()
    microscope = hub.capture_microscope(permission)
    thermal = hub.capture_thermal_camera(permission)
    meter = hub.read_multimeter(permission)
    supply = hub.read_power_supply(permission)
    assert microscope.data["image"] is None
    assert thermal.data["image"] is None
    assert meter.data["value"] is None
    assert supply.data["voltage"] is None
    assert all(item.is_mock for item in (microscope, thermal, meter, supply))
