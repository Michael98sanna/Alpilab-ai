"""Windows auto-start registration for ALPILAB AI."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("alpilab.local_hub")

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE_NAME = "ALPILAB AI"


def _autostart_command() -> str:
    exe = Path(sys.executable).resolve()
    # Quote path to support spaces in "ALPILAB AI.exe".
    return f'"{exe}"'


def ensure_windows_autostart(enabled: bool) -> None:
    """Ensure HKCU Run registration matches configuration on Windows only."""
    if sys.platform != "win32":
        return
    try:
        import winreg
    except ImportError:
        logger.warning("winreg unavailable; skipping Windows auto-start setup")
        return

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
            if not enabled:
                try:
                    winreg.DeleteValue(key, _RUN_VALUE_NAME)
                    logger.info("Windows auto-start disabled")
                except FileNotFoundError:
                    pass
                return

            desired = _autostart_command()
            try:
                current, _ = winreg.QueryValueEx(key, _RUN_VALUE_NAME)
            except FileNotFoundError:
                current = None
            if current == desired:
                return
            winreg.SetValueEx(key, _RUN_VALUE_NAME, 0, winreg.REG_SZ, desired)
            logger.info("Windows auto-start enabled")
    except OSError as exc:
        logger.warning("Failed to configure Windows auto-start: %s", exc)
