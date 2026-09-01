"""Collect panic-full logs from a connected iPhone."""

from __future__ import annotations

import asyncio
import glob
import logging
import os
import tempfile
from pathlib import Path

from pc_agent.win_no_console import windows_no_console_kwargs

from .config import find_libimobiledevice_binary

logger = logging.getLogger(__name__)

_SUBPROCESS_FLAGS = windows_no_console_kwargs()


class PanicLogCollector:
    """Extract panic logs from device via idevicecrashreport."""

    def __init__(self) -> None:
        binary = find_libimobiledevice_binary("idevicecrashreport.exe")
        self.idevicecrashreport_path = str(binary) if binary else None

    async def collect_latest(self, device_id: str) -> Path | None:
        """Copy crash reports and return newest panic-full-*.ips path."""
        try:
            if not self.idevicecrashreport_path:
                logger.error("idevicecrashreport not found")
                return None

            temp_base = Path(tempfile.gettempdir()) / "alpilab" / "iphone_panic"
            temp_base.mkdir(parents=True, exist_ok=True)
            temp_dir = temp_base / device_id
            temp_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                self.idevicecrashreport_path,
                "-k",
                "-u",
                device_id,
                str(temp_dir),
            ]
            logger.info("Collecting panic logs from %s", device_id)
            await self._run_cmd(cmd, timeout=30)

            panic_files = glob.glob(str(temp_dir / "panic-full-*.ips"))
            if not panic_files:
                panic_files = glob.glob(str(temp_dir / "**" / "panic-full-*.ips"), recursive=True)

            if not panic_files:
                logger.info("No panic log found for device %s", device_id)
                return None

            panic_files.sort(key=os.path.getmtime, reverse=True)
            latest = Path(panic_files[0])
            logger.info("Found panic log: %s", latest.name)
            return latest
        except Exception as exc:
            logger.error("Error collecting panic log: %s", exc)
            return None

    async def _run_cmd(self, cmd: list[str], timeout: int = 30) -> str | None:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **_SUBPROCESS_FLAGS,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            if process.returncode != 0:
                logger.warning("Command stderr: %s", stderr.decode(errors="ignore"))
            output = stdout.decode("utf-8", errors="ignore").strip()
            return output or "ok"
        except asyncio.TimeoutError:
            logger.error("Command timeout")
            return None
        except Exception as exc:
            logger.error("Error: %s", exc)
            return None
