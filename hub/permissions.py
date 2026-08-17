"""Named Hub actions and helpers to build permission contexts."""

from __future__ import annotations

from app.core.security import PermissionContext

OPEN_APPLICATION = "open_application"
CLOSE_APPLICATION = "close_application"
CAPTURE_MICROSCOPE = "capture_microscope"
CAPTURE_THERMAL_CAMERA = "capture_thermal_camera"
READ_MULTIMETER = "read_multimeter"
READ_POWER_SUPPLY = "read_power_supply"
GET_PC_STATUS = "get_pc_status"

HUB_ACTIONS: frozenset[str] = frozenset(
    {
        OPEN_APPLICATION,
        CLOSE_APPLICATION,
        CAPTURE_MICROSCOPE,
        CAPTURE_THERMAL_CAMERA,
        READ_MULTIMETER,
        READ_POWER_SUPPLY,
        GET_PC_STATUS,
    }
)

DANGEROUS_ACTIONS: frozenset[str] = frozenset({CLOSE_APPLICATION})


def full_lab_permissions(actor: str = "lab") -> PermissionContext:
    return PermissionContext(actor=actor, allowed_actions=HUB_ACTIONS)
