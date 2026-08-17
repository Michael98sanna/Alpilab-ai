"""Alpilab Check bridge — abstract connector only.

Alpilab Check is a separate Windows desktop app. Alpilab AI must NEVER import
its internal code. Future communication will use a stable API / file / HTTP /
local-bridge contract defined here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class CheckDeviceSnapshot(BaseModel):
    """Normalized device data as received from Alpilab Check (conceptual)."""

    brand: str | None = None
    model: str | None = None
    identifier: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class CheckDiagnosticPayload(BaseModel):
    """Normalized diagnostic payload from Alpilab Check (conceptual)."""

    session_ref: str | None = None
    tests: list[dict[str, Any]] = Field(default_factory=list)
    measurements: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AlpilabCheckConnector(ABC):
    """Future bridge between Alpilab AI and Alpilab Check.

    Transport is intentionally unspecified (HTTP, local socket, file drop, …).
    """

    name: str = "alpilab_check"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when a Check bridge endpoint is reachable."""

    @abstractmethod
    def fetch_device_snapshot(self, reference: str) -> CheckDeviceSnapshot:
        """Fetch device identity data for a Check-side reference id."""

    @abstractmethod
    def fetch_diagnostics(self, reference: str) -> CheckDiagnosticPayload:
        """Fetch diagnostic results linked to a Check-side session/reference."""


class MockAlpilabCheckConnector(AlpilabCheckConnector):
    """MOCK: returns deterministic placeholder payloads. No real Check link."""

    name = "alpilab_check_mock"

    def is_available(self) -> bool:
        return True

    def fetch_device_snapshot(self, reference: str) -> CheckDeviceSnapshot:
        return CheckDeviceSnapshot(
            brand="MockBrand",
            model="MockPhone",
            identifier=reference,
            raw={"mock": True, "reference": reference},
        )

    def fetch_diagnostics(self, reference: str) -> CheckDiagnosticPayload:
        return CheckDiagnosticPayload(
            session_ref=reference,
            tests=[{"name": "mock_boot_test", "status": "passed"}],
            measurements=[{"name": "mock_voltage", "value": "0", "unit": "V"}],
            raw={"mock": True},
        )
