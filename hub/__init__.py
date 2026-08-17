"""Alpilab Hub: future Windows bridge between cloud and lab PC hardware/software.

This package defines the contract only. Nothing here launches Windows programs,
runs shell commands, or exposes a remote shell.
"""

from .base import AlpilabHub, HubResult, KnownApplication
from .mock import MockAlpilabHub
from .permissions import HUB_ACTIONS, full_lab_permissions

__all__ = [
    "AlpilabHub",
    "HubResult",
    "KnownApplication",
    "MockAlpilabHub",
    "HUB_ACTIONS",
    "full_lab_permissions",
]
