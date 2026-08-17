"""Alpilab Hub - future Windows bridge between cloud and local hardware."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HubCapability(str, Enum):
    """Capabilities that Alpilab Hub may expose."""

    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    CAPTURE_MICROSCOPE = "capture_microscope"
    CAPTURE_THERMAL_CAMERA = "capture_thermal_camera"
    READ_MULTIMETER = "read_multimeter"
    READ_POWER_SUPPLY = "read_power_supply"
    GET_PC_STATUS = "get_pc_status"


class HubActionResult(BaseModel):
    """Result of a Hub action request."""

    success: bool
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False


class PCStatus(BaseModel):
    """High-level status of the connected Windows workstation."""

    online: bool = False
    hostname: str | None = None
    connected_devices: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlpilabHub(ABC):
    """
    Future local service on the Windows PC (Alpilab Hub).

    This interface does NOT execute shell commands or arbitrary programs.
    Real implementations will require explicit permissions and user confirmation
    for potentially dangerous actions.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the Hub endpoint is reachable."""

    @abstractmethod
    def capabilities(self) -> set[HubCapability]:
        """Return supported Hub capabilities."""

    @abstractmethod
    def open_application(self, application_name: str) -> HubActionResult:
        """Request opening a supported desktop application."""

    @abstractmethod
    def close_application(self, application_name: str) -> HubActionResult:
        """Request closing a supported desktop application."""

    @abstractmethod
    def capture_microscope(self) -> HubActionResult:
        """Request a microscope image capture."""

    @abstractmethod
    def capture_thermal_camera(self) -> HubActionResult:
        """Request a thermal camera capture."""

    @abstractmethod
    def read_multimeter(self) -> HubActionResult:
        """Read the latest multimeter measurement."""

    @abstractmethod
    def read_power_supply(self) -> HubActionResult:
        """Read the bench power supply status."""

    @abstractmethod
    def get_pc_status(self) -> PCStatus:
        """Return workstation connectivity and device status."""
