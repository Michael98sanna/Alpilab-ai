"""Abstract capability surface for Alpilab Hub."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PcStatus:
    online: bool
    hostname: str | None = None
    os_name: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HubActionResult:
    """Result of a Hub capability call.

    ``requires_confirmation`` / ``confirmed`` prepare the future permission model.
    Mock implementations never perform real side effects.
    """

    success: bool
    action: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmed: bool = False
    mock: bool = True
    timestamp: datetime = field(default_factory=_utcnow)


class AlpilabHub(ABC):
    """Bridge contract between Alpilab AI cloud and a lab Windows PC.

    Implementations must never expose arbitrary command execution.
    Each capability is an explicit, allow-listed action.
    """

    name: str = "alpilab_hub"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_pc_status(self) -> PcStatus:
        raise NotImplementedError

    @abstractmethod
    def open_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        """Open a known allow-listed application (future)."""
        raise NotImplementedError

    @abstractmethod
    def close_application(self, app_id: str, *, confirmed: bool = False) -> HubActionResult:
        """Close a known allow-listed application (future)."""
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
