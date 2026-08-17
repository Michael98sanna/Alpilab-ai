"""Alpilab Hub — future Windows PC bridge (interfaces + mock only).

IMPORTANT:
- Does NOT execute real Windows programs.
- Does NOT run arbitrary shell commands.
- Does NOT provide a remote shell.
- Hardware/software control is mock-only in this phase.
"""

from hub.base import AlpilabHub, HubCapability, HubPCStatus
from hub.mock import MockAlpilabHub

__all__ = [
    "AlpilabHub",
    "HubCapability",
    "HubPCStatus",
    "MockAlpilabHub",
]
