"""Alpilab Hub — future Windows bridge between cloud and local bench tools.

IMPORTANT (foundation phase):
- Only interfaces and mocks live here.
- Do NOT execute Windows programs.
- Do NOT run arbitrary shell commands.
- Do NOT implement remote shell.
- Dangerous/hardware actions will require permissions + explicit confirmation later.
"""

from hub.interface import AlpilabHub, HubActionResult, PcStatus
from hub.mock import MockAlpilabHub

__all__ = ["AlpilabHub", "HubActionResult", "MockAlpilabHub", "PcStatus"]
