"""Abstract Hub contract. Implementations must not execute arbitrary commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, Field

from app.core.security import PermissionContext


class KnownApplication(str, Enum):
    """Logical application ids. Not filesystem paths or shell commands."""

    ALPILAB_CHECK = "alpilab_check"
    THREE_UTOOLS = "3utools"
    BORNEO = "borneo"
    ZXW = "zxw"


class HubResult(BaseModel):
    """Result of a Hub call. is_mock must stay True until a real Hub exists."""

    ok: bool
    action: str
    is_mock: bool = True
    message: str
    data: dict[str, object] = Field(default_factory=dict)


class AlpilabHub(ABC):
    """Windows-side bridge. Cloud code talks to this interface, never to the OS."""

    name: str = "alpilab_hub"

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def get_pc_status(self, permission: PermissionContext) -> HubResult: ...

    @abstractmethod
    def open_application(
        self,
        application: KnownApplication,
        permission: PermissionContext,
    ) -> HubResult: ...

    @abstractmethod
    def close_application(
        self,
        application: KnownApplication,
        permission: PermissionContext,
        *,
        confirmed: bool = False,
    ) -> HubResult: ...

    @abstractmethod
    def capture_microscope(self, permission: PermissionContext) -> HubResult: ...

    @abstractmethod
    def capture_thermal_camera(self, permission: PermissionContext) -> HubResult: ...

    @abstractmethod
    def read_multimeter(self, permission: PermissionContext) -> HubResult: ...

    @abstractmethod
    def read_power_supply(self, permission: PermissionContext) -> HubResult: ...
