"""Abstract Hub interface for future PC / hardware / software bridging."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HubCapability(str, Enum):
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    CAPTURE_MICROSCOPE = "capture_microscope"
    CAPTURE_THERMAL_CAMERA = "capture_thermal_camera"
    READ_MULTIMETER = "read_multimeter"
    READ_POWER_SUPPLY = "read_power_supply"
    GET_PC_STATUS = "get_pc_status"


@dataclass
class HubPCStatus:
    online: bool
    hostname: str | None = None
    os_name: str | None = None
    capabilities: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HubActionResult:
    """Result of a Hub action. Mock results are always flagged."""

    success: bool
    action: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    is_mock: bool = True
    requires_confirmation: bool = False


class AlpilabHub(ABC):
    """Contract for the future Alpilab Hub Windows service."""

    name: str = "alpilab_hub"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_pc_status(self) -> HubPCStatus:
        raise NotImplementedError

    @abstractmethod
    def open_application(
        self, application_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def close_application(
        self, application_id: str, *, confirmed: bool = False
    ) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_microscope(self, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def capture_thermal_camera(self, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_multimeter(self, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError

    @abstractmethod
    def read_power_supply(self, *, confirmed: bool = False) -> HubActionResult:
        raise NotImplementedError
