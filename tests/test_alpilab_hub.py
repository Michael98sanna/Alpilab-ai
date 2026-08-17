"""Tests for the Alpilab Hub mock. It must never execute real commands."""

import pytest

from app.core.security import (
    ConfirmationRequiredError,
    PermissionContext,
    PermissionDeniedError,
    SAFE_READ_CAPABILITIES,
)
from hub.mock import MockAlpilabHub
from hub.schemas import ApplicationActionRequest


def _full_permissions() -> PermissionContext:
    return PermissionContext(
        actor="tester",
        allowed_capabilities=SAFE_READ_CAPABILITIES
        | frozenset({"open_application", "close_application"}),
    )


def test_hub_status_is_mock() -> None:
    hub = MockAlpilabHub()
    status = hub.get_pc_status(PermissionContext())
    assert status.is_mock is True
    assert status.reachable is True
    assert "get_pc_status" in status.capabilities


def test_hub_read_capabilities_do_not_execute() -> None:
    hub = MockAlpilabHub()
    permissions = PermissionContext()

    microscope = hub.capture_microscope(permissions)
    thermal = hub.capture_thermal_camera(permissions)
    meter = hub.read_multimeter(permissions)
    psu = hub.read_power_supply(permissions)

    for result in (microscope, thermal, meter, psu):
        assert result.is_mock is True
        assert result.executed is False
        assert result.ok is True


def test_open_application_requires_confirmation() -> None:
    hub = MockAlpilabHub()
    with pytest.raises(ConfirmationRequiredError):
        hub.open_application(
            ApplicationActionRequest(application="3utools", confirmed=False),
            _full_permissions(),
        )


def test_open_application_accepted_but_not_executed() -> None:
    hub = MockAlpilabHub()
    result = hub.open_application(
        ApplicationActionRequest(application="3utools", confirmed=True),
        _full_permissions(),
    )
    assert result.ok is True
    assert result.executed is False
    assert result.is_mock is True
    assert "NON eseguita" in result.message


def test_unknown_application_is_rejected_without_execution() -> None:
    hub = MockAlpilabHub()
    result = hub.open_application(
        ApplicationActionRequest(application="cmd.exe && format C:", confirmed=True),
        _full_permissions(),
    )
    assert result.ok is False
    assert result.executed is False
    assert "allow-list" in result.message


def test_missing_permission_is_denied() -> None:
    hub = MockAlpilabHub()
    with pytest.raises(PermissionDeniedError):
        hub.open_application(
            ApplicationActionRequest(application="3utools", confirmed=True),
            PermissionContext(),
        )
