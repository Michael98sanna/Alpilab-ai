"""Windows helpers to run auxiliary console processes without a visible window."""

from __future__ import annotations

import subprocess
import sys
from typing import Any


def windows_no_console_kwargs() -> dict[str, Any]:
    """
    Kwargs for subprocess / asyncio.create_subprocess_exec on Windows.

    Combines CREATE_NO_WINDOW with STARTUPINFO(SW_HIDE) so console subsystem
    helpers (adb.exe, tasklist, powershell) do not flash a CMD window.
    Empty on non-Windows.
    """
    if sys.platform != "win32":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }
