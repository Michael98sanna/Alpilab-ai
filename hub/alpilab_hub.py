"""Alpilab Hub — future Windows PC bridge (interfaces and mocks only).

IMPORTANT:
- Does NOT execute Windows programs.
- Does NOT run arbitrary shell commands.
- Does NOT provide remote shell capabilities.
- Dangerous actions will require explicit confirmation (see app.core.security).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.security import requires_confirmation


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class HubActionResult:
    """Result of a Hub capability call."""

    ok: bool
    action: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmed: bool = False
    mock: bool = False
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class PCStatus:
    """High-level Hub host status."""

    online: bool
    hostname: str | None = None
    os_name: str | None = None
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AlpilabHub(ABC):
    """Contract for the future Windows Hub service."""

    name: str = "alpilab_hub"

    @abstractmethod
    def get_pc_status(self) -> PCStatus:
        raise NotImplementedError

    @abstractmethod
    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_microscope(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_thermal_camera(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_multimeter(self) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_power_supply(self) -> HubActionResult:
        raise NotImplementedError


class MockAlpilabHub(AlpilabHub):
    """MOCK Hub. Returns placeholders and never touches the OS."""

    name = "alpilab_hub_mock"

    def get_pc_status(self) -> PCStatus:
        return PCStatus(
            online=True,
            hostname="mock-hub-pc",
            os_name="Windows (mock)",
            capabilities=[
                "open_application",
                "close_application",
                "capture_microscope",
                "capture_thermal_camera",
                "read_multimeter",
                "read_power_supply",
                "get_pc_status",
            ],
            metadata={"mock": True},
        )

    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        return self._guarded_app_action("open_application", app_id, confirmed)

    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        return self._guarded_app_action("close_application", app_id, confirmed)

    def capture_microscope(self) -> HubActionResult:
        return HubActionResult(
            ok=True,
            action="capture_microscope",
            message="MOCK: microscope capture not connected.",
            data={"image_ref": None},
            mock=True,
        )

    def capture_thermal_camera(self) -> HubActionResult:
        return HubActionResult(
            ok=True,
            action="capture_thermal_camera",
            message="MOCK: thermal camera capture not connected.",
            data={"image_ref": None},
            mock=True,
        )

    def read_multimeter(self) -> HubActionResult:
        return HubActionResult(
            ok=True,
            action="read_multimeter",
            message="MOCK: multimeter not connected.",
            data={"value": None, "unit": None},
            mock=True,
        )

    def read_power_supply(self) -> HubActionResult:
        return HubActionResult(
            ok=True,
            action="read_power_supply",
            message="MOCK: power supply not connected.",
            data={"voltage": None, "current": None},
            mock=True,
        )

    def _guarded_app_action(
        self,
        action: str,
        app_id: str,
        confirmed: bool,
    ) -> HubActionResult:
        needs_confirm = requires_confirmation(action)
        if needs_confirm and not confirmed:
            return HubActionResult(
                ok=False,
                action=action,
                message=(
                    f"Confirmation required before '{action}' for app '{app_id}'. "
                    "No OS command was executed."
                ),
                data={"app_id": app_id},
                requires_confirmation=True,
                confirmed=False,
                mock=True,
            )
        return HubActionResult(
            ok=True,
            action=action,
            message=(
                f"MOCK: would {action.replace('_', ' ')} '{app_id}'. "
                "No OS command was executed."
            ),
            data={"app_id": app_id},
            requires_confirmation=needs_confirm,
            confirmed=confirmed,
            mock=True,
        )
