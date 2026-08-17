"""Alpilab Hub — conceptual Windows PC bridge (interfaces + mocks only).

IMPORTANT:
- Does NOT execute Windows programs
- Does NOT run arbitrary shell commands
- Does NOT provide remote shell
- Hardware/software control is future work behind permissions + confirmation
"""

from hub.client import AlpilabHub, MockAlpilabHub
from hub.schemas import HubActionResult, PCStatus

__all__ = ["AlpilabHub", "MockAlpilabHub", "HubActionResult", "PCStatus"]
