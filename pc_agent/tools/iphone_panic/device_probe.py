"""On-demand iPhone detection via libimobiledevice."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from pc_agent.win_no_console import windows_no_console_kwargs

from .config import find_libimobiledevice_binary

logger = logging.getLogger(__name__)

_SUBPROCESS_FLAGS = windows_no_console_kwargs()


class iOSDeviceProbe:
    """Detect connected iPhone using libimobiledevice binaries."""

    def __init__(self) -> None:
        idevice_id = find_libimobiledevice_binary("idevice_id.exe")
        ideviceinfo = find_libimobiledevice_binary("ideviceinfo.exe")
        self.idevice_id_path = str(idevice_id) if idevice_id else None
        self.ideviceinfo_path = str(ideviceinfo) if ideviceinfo else None

    async def probe_device(self) -> dict[str, str] | None:
        """Return device metadata or None if unavailable."""
        try:
            if not self.idevice_id_path or not self.ideviceinfo_path:
                logger.error("idevice_id or ideviceinfo not found")
                return None

            listing = await self._run_cmd([self.idevice_id_path, "-l"], timeout=5)
            if not listing:
                logger.info("No iOS device found")
                return None

            udids = [line.strip() for line in listing.splitlines() if line.strip()]
            if not udids:
                logger.info("No iOS device found")
                return None

            udid = udids[0]
            logger.info("Found iOS device: %s", udid)
            device_info = await self._get_device_info(udid)
            if not device_info:
                return None

            return {
                "device_id": udid,
                "model": device_info.get("ProductType", "unknown"),
                "device_name": device_info.get("DeviceName", "iPhone"),
                "ios_version": device_info.get("ProductVersion", "unknown"),
            }
        except Exception as exc:
            logger.error("Error probing device: %s", exc)
            return None

    async def _get_device_info(self, udid: str) -> dict[str, str] | None:
        keys = ["ProductType", "ProductVersion", "DeviceName"]
        info: dict[str, str] = {}
        for key in keys:
            value = await self._run_cmd(
                [self.ideviceinfo_path, "-u", udid, "-k", key],
                timeout=5,
            )
            if value:
                info[key] = value.strip()
        return info or None

    async def _run_cmd(self, cmd: list[str], timeout: int = 5) -> str | None:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **_SUBPROCESS_FLAGS,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            if process.returncode != 0:
                logger.warning("Command failed (%s): %s", cmd[0], stderr.decode(errors="ignore"))
                return None
            return stdout.decode("utf-8", errors="ignore")
        except asyncio.TimeoutError:
            logger.error("Command timeout: %s", " ".join(cmd))
            return None
        except Exception as exc:
            logger.error("Error running command: %s", exc)
            return None
