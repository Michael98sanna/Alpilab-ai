"""ADB-based device scanner for detecting Android phones connected via USB."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("alpilab.device_scanner")

ADB_SCAN_INTERVAL = 2.0


@dataclass(frozen=True)
class ScannedDevice:
    """A device detected by ADB."""

    serial: str
    state: str  # "device", "offline", "unauthorized"
    transport_id: str | None = None
    product: str | None = None
    model_code: str | None = None
    device_code: str | None = None
    brand: str | None = None
    model_name: str | None = None
    market_name: str | None = None

    def to_detected_dict(self) -> dict[str, Any]:
        """Convert to a dict compatible with DetectedDevice schema."""
        display_model = self.market_name or self.model_name or self.model_code
        return {
            "id": f"adb-{self.serial}",
            "brand": self.brand,
            "model": display_model,
            "variant": self.model_code if self.market_name else None,
            "serial_number": self.serial,
            "connection_type": "usb",
            "source": "adb",
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "adb_state": self.state,
                "transport_id": self.transport_id,
                "product": self.product,
                "device_code": self.device_code,
            },
        }


def _find_adb() -> str | None:
    """Locate adb executable."""
    env_adb = os.getenv("ALPILAB_ADB_PATH")
    if env_adb and os.path.isfile(env_adb):
        return env_adb
    # Standard Android SDK location on Windows
    local = os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe")
    if os.path.isfile(local):
        return local
    return shutil.which("adb")


async def _run_adb(adb_path: str, *args: str) -> str | None:
    """Run an ADB command and return stdout, or None on error."""
    try:
        proc = await asyncio.create_subprocess_exec(
            adb_path, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
        if proc.returncode != 0:
            return None
        return stdout.decode("utf-8", errors="replace")
    except Exception:
        return None


def _parse_devices_output(output: str) -> list[dict[str, str]]:
    """Parse `adb devices -l` output into a list of dicts."""
    devices: list[dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("List of") or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial = parts[0]
        state = parts[1]
        info: dict[str, str] = {"serial": serial, "state": state}
        for token in parts[2:]:
            if ":" in token:
                key, _, val = token.partition(":")
                info[key] = val
        devices.append(info)
    return devices


async def _get_prop(adb_path: str, serial: str, prop: str) -> str | None:
    out = await _run_adb(adb_path, "-s", serial, "shell", "getprop", prop)
    if out:
        val = out.strip()
        return val if val else None
    return None


async def _enrich_device(adb_path: str, raw: dict[str, str]) -> ScannedDevice:
    """Build a ScannedDevice, fetching props if the device is online."""
    serial = raw["serial"]
    state = raw["state"]
    brand = None
    model_name = None
    market_name = None

    if state == "device":
        brand, model_name, market_name = await asyncio.gather(
            _get_prop(adb_path, serial, "ro.product.brand"),
            _get_prop(adb_path, serial, "ro.product.model"),
            _get_prop(adb_path, serial, "ro.product.marketname"),
        )

    return ScannedDevice(
        serial=serial,
        state=state,
        transport_id=raw.get("transport_id"),
        product=raw.get("product"),
        model_code=raw.get("model"),
        device_code=raw.get("device"),
        brand=brand.capitalize() if brand else None,
        model_name=model_name,
        market_name=market_name,
    )


async def scan_devices(adb_path: str | None = None) -> list[ScannedDevice]:
    """Scan for connected Android devices via ADB."""
    adb = adb_path or _find_adb()
    if not adb:
        logger.debug("ADB not found")
        return []

    output = await _run_adb(adb, "devices", "-l")
    if output is None:
        return []

    raw_list = _parse_devices_output(output)
    if not raw_list:
        return []

    tasks = [_enrich_device(adb, raw) for raw in raw_list]
    return list(await asyncio.gather(*tasks))


class DeviceScanner:
    """Background scanner that polls ADB and notifies on list changes."""

    def __init__(
        self,
        on_change: Any = None,
        interval: float = ADB_SCAN_INTERVAL,
        adb_path: str | None = None,
    ) -> None:
        self._on_change = on_change
        self._interval = interval
        self._adb_path = adb_path
        self._previous_ids: set[str] = set()
        self._previous_devices: list[ScannedDevice] = []
        self._task: asyncio.Task[None] | None = None

    @property
    def current_devices(self) -> list[ScannedDevice]:
        return list(self._previous_devices)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())
            logger.info("Device scanner started (interval=%.1fs)", self._interval)

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Device scanner stopped")

    async def _loop(self) -> None:
        try:
            while True:
                try:
                    await self._poll()
                except Exception:
                    logger.debug("Scanner poll error", exc_info=True)
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            pass

    async def _poll(self) -> None:
        devices = await scan_devices(self._adb_path)
        current_ids = {d.serial for d in devices}

        if current_ids == self._previous_ids:
            # Check if states changed (e.g. unauthorized → device)
            prev_states = {d.serial: d.state for d in self._previous_devices}
            curr_states = {d.serial: d.state for d in devices}
            if prev_states == curr_states:
                return

        self._previous_ids = current_ids
        self._previous_devices = devices
        logger.info("Device list changed: %d device(s)", len(devices))

        if self._on_change:
            detected = [d.to_detected_dict() for d in devices if d.state == "device"]
            await self._on_change(detected)
