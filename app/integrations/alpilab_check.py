"""Abstract connector for future Alpilab Check integration."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CheckDeviceInfo(BaseModel):
    """Device data that Alpilab Check may expose in the future."""

    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    serial_number: str | None = None
    imei: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CheckDiagnosticSnapshot(BaseModel):
    """Diagnostic snapshot that Alpilab Check may export."""

    session_reference: str
    tests: list[dict[str, Any]] = Field(default_factory=list)
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    captured_at: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """
    Future bridge to Alpilab Check without importing its internal code.

    Integration may happen via HTTP API, local bridge, files, or another
    stable contract. This interface defines only the expected capabilities.
    """

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether Alpilab Check is reachable."""

    @abstractmethod
    def get_device_info(self, device_reference: str) -> CheckDeviceInfo | None:
        """Fetch device identification data from Alpilab Check."""

    @abstractmethod
    def get_diagnostic_snapshot(
        self, session_reference: str
    ) -> CheckDiagnosticSnapshot | None:
        """Fetch a diagnostic snapshot for a repair/check session."""

    @abstractmethod
    def push_repair_update(self, payload: dict[str, Any]) -> bool:
        """Send repair progress back to Alpilab Check when supported."""
