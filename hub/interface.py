"""Abstract Hub contract.

Implementations must never provide a generic command runner.
Each capability is a named, permissioned, optionally confirmed action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.security import PermissionContext

from .schemas import ApplicationActionRequest, HubResult, PcStatus


class AlpilabHub(ABC):
    """Bench-PC bridge. Phase 1: interface only."""

    @abstractmethod
    def get_pc_status(self, permissions: PermissionContext) -> PcStatus:
        """Read-only status of the PC / Hub agent."""

    @abstractmethod
    def open_application(
        self,
        request: ApplicationActionRequest,
        permissions: PermissionContext,
    ) -> HubResult:
        """Open a known application. Requires permission and confirmation."""

    @abstractmethod
    def close_application(
        self,
        request: ApplicationActionRequest,
        permissions: PermissionContext,
    ) -> HubResult:
        """Close a known application. Requires permission and confirmation."""

    @abstractmethod
    def capture_microscope(self, permissions: PermissionContext) -> HubResult:
        """Capture a still from a connected microscope. Not implemented."""

    @abstractmethod
    def capture_thermal_camera(self, permissions: PermissionContext) -> HubResult:
        """Capture a frame from a thermal camera. Not implemented."""

    @abstractmethod
    def read_multimeter(self, permissions: PermissionContext) -> HubResult:
        """Read the current multimeter value. Not implemented."""

    @abstractmethod
    def read_power_supply(self, permissions: PermissionContext) -> HubResult:
        """Read voltage/current from the bench PSU. Not implemented."""
