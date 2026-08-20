"""Tests for V0.6 Milestone 2 — PC Agent Device Scanner."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pc_agent.device_scanner import (
    DeviceScanner,
    ScannedDevice,
    _SUBPROCESS_FLAGS,
    _parse_devices_output,
    _run_adb,
    scan_devices,
)

# ---------------------------------------------------------------------------
# Fixtures: mock ADB outputs
# ---------------------------------------------------------------------------

ADB_ZERO = "List of devices attached\n\n"

ADB_ONE = """\
List of devices attached
RFCY11GRHTZ            device product:pa1qxeea model:SM_S931B device:pa1q transport_id:3

"""

ADB_TWO = """\
List of devices attached
RFCY11GRHTZ            device product:pa1qxeea model:SM_S931B device:pa1q transport_id:3
ABC123456              device product:coral model:Pixel_4_XL device:coral transport_id:5

"""

ADB_UNAUTHORIZED = """\
List of devices attached
RFCY11GRHTZ            unauthorized transport_id:3

"""

ADB_OFFLINE = """\
List of devices attached
RFCY11GRHTZ            offline transport_id:3

"""

ADB_MIXED = """\
List of devices attached
RFCY11GRHTZ            device product:pa1qxeea model:SM_S931B device:pa1q transport_id:3
ABC123456              unauthorized transport_id:5

"""

PROP_BRAND = "samsung\n"
PROP_MODEL = "SM-S931B\n"
PROP_MARKET = "Galaxy S24\n"


# ---------------------------------------------------------------------------
# 1. Parse adb devices output
# ---------------------------------------------------------------------------

class TestParseDevices:
    def test_zero_devices(self):
        assert _parse_devices_output(ADB_ZERO) == []

    def test_one_device(self):
        result = _parse_devices_output(ADB_ONE)
        assert len(result) == 1
        assert result[0]["serial"] == "RFCY11GRHTZ"
        assert result[0]["state"] == "device"
        assert result[0]["model"] == "SM_S931B"

    def test_two_devices(self):
        result = _parse_devices_output(ADB_TWO)
        assert len(result) == 2

    def test_unauthorized(self):
        result = _parse_devices_output(ADB_UNAUTHORIZED)
        assert len(result) == 1
        assert result[0]["state"] == "unauthorized"

    def test_offline(self):
        result = _parse_devices_output(ADB_OFFLINE)
        assert len(result) == 1
        assert result[0]["state"] == "offline"


# ---------------------------------------------------------------------------
# 2-6. scan_devices with mocked ADB
# ---------------------------------------------------------------------------

async def _mock_run_adb(adb_path, *args):
    cmd = " ".join(args)
    if "devices" in cmd:
        return ADB_ONE
    if "ro.product.brand" in cmd:
        return PROP_BRAND
    if "ro.product.model" in cmd:
        return PROP_MODEL
    if "ro.product.marketname" in cmd:
        return PROP_MARKET
    return None


async def _mock_run_adb_zero(adb_path, *args):
    if "devices" in args:
        return ADB_ZERO
    return None


async def _mock_run_adb_two(adb_path, *args):
    cmd = " ".join(args)
    if "devices" in cmd:
        return ADB_TWO
    if "ro.product.brand" in cmd:
        return PROP_BRAND
    if "ro.product.model" in cmd:
        return PROP_MODEL
    if "ro.product.marketname" in cmd:
        return PROP_MARKET
    return None


async def _mock_run_adb_unauthorized(adb_path, *args):
    cmd = " ".join(args)
    if "devices" in cmd:
        return ADB_UNAUTHORIZED
    return None


class TestScanDevices:
    @pytest.mark.asyncio
    async def test_zero_devices(self):
        with patch("pc_agent.device_scanner._run_adb", side_effect=_mock_run_adb_zero):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                result = await scan_devices()
        assert result == []

    @pytest.mark.asyncio
    async def test_one_device(self):
        with patch("pc_agent.device_scanner._run_adb", side_effect=_mock_run_adb):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                result = await scan_devices()
        assert len(result) == 1
        d = result[0]
        assert d.serial == "RFCY11GRHTZ"
        assert d.state == "device"
        assert d.brand == "Samsung"
        assert d.model_name == "SM-S931B"
        assert d.market_name == "Galaxy S24"

    @pytest.mark.asyncio
    async def test_two_devices(self):
        with patch("pc_agent.device_scanner._run_adb", side_effect=_mock_run_adb_two):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                result = await scan_devices()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_unauthorized_not_enriched(self):
        with patch("pc_agent.device_scanner._run_adb", side_effect=_mock_run_adb_unauthorized):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                result = await scan_devices()
        assert len(result) == 1
        d = result[0]
        assert d.state == "unauthorized"
        assert d.brand is None
        assert d.model_name is None

    @pytest.mark.asyncio
    async def test_adb_not_found(self):
        with patch("pc_agent.device_scanner._find_adb", return_value=None):
            result = await scan_devices()
        assert result == []

    @pytest.mark.asyncio
    async def test_adb_error_returns_empty(self):
        async def failing_adb(*args):
            return None
        with patch("pc_agent.device_scanner._run_adb", side_effect=failing_adb):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                result = await scan_devices()
        assert result == []


# ---------------------------------------------------------------------------
# 7. ScannedDevice.to_detected_dict
# ---------------------------------------------------------------------------

class TestToDetectedDict:
    def test_full_device(self):
        d = ScannedDevice(
            serial="RFCY11GRHTZ",
            state="device",
            brand="Samsung",
            model_name="SM-S931B",
            market_name="Galaxy S24",
            model_code="SM_S931B",
        )
        out = d.to_detected_dict()
        assert out["id"] == "adb-RFCY11GRHTZ"
        assert out["brand"] == "Samsung"
        assert out["model"] == "Galaxy S24"
        assert out["variant"] == "SM_S931B"
        assert out["source"] == "adb"
        assert out["connection_type"] == "usb"

    def test_unauthorized_device(self):
        d = ScannedDevice(serial="XYZ", state="unauthorized")
        out = d.to_detected_dict()
        assert out["brand"] is None
        assert out["metadata"]["adb_state"] == "unauthorized"


# ---------------------------------------------------------------------------
# 8-10. DeviceScanner polling and change detection
# ---------------------------------------------------------------------------

class TestDeviceScanner:
    @pytest.mark.asyncio
    async def test_callback_on_change(self):
        callback = AsyncMock()
        scanner = DeviceScanner(on_change=callback, interval=0.05)

        call_count = 0
        async def mock_scan_first(*a):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [ScannedDevice(serial="A", state="device", brand="Samsung", model_name="Test")]
            return [ScannedDevice(serial="A", state="device", brand="Samsung", model_name="Test")]

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan_first):
            scanner.start()
            await asyncio.sleep(0.2)
            scanner.stop()

        # Called once when first device appears (empty -> [A])
        assert callback.call_count >= 1

    @pytest.mark.asyncio
    async def test_no_callback_when_unchanged(self):
        callback = AsyncMock()
        scanner = DeviceScanner(on_change=callback, interval=0.05)

        device = ScannedDevice(serial="A", state="device")
        scanner._previous_ids = {"A"}
        scanner._previous_devices = [device]

        async def mock_scan_same(*a):
            return [device]

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan_same):
            scanner.start()
            await asyncio.sleep(0.2)
            scanner.stop()

        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_on_device_removed(self):
        callback = AsyncMock()
        scanner = DeviceScanner(on_change=callback, interval=0.05)

        device = ScannedDevice(serial="A", state="device")
        scanner._previous_ids = {"A"}
        scanner._previous_devices = [device]

        async def mock_scan_empty(*a):
            return []

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan_empty):
            scanner.start()
            await asyncio.sleep(0.2)
            scanner.stop()

        assert callback.call_count >= 1
        # Called with empty list
        callback.assert_called_with([])

    @pytest.mark.asyncio
    async def test_only_authorized_in_callback(self):
        """Only devices with state='device' are sent in the callback."""
        callback = AsyncMock()
        scanner = DeviceScanner(on_change=callback, interval=0.05)

        async def mock_scan_mixed(*a):
            return [
                ScannedDevice(serial="A", state="device", brand="Samsung", model_name="Test"),
                ScannedDevice(serial="B", state="unauthorized"),
            ]

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan_mixed):
            scanner.start()
            await asyncio.sleep(0.2)
            scanner.stop()

        assert callback.call_count >= 1
        devices_arg = callback.call_args[0][0]
        assert len(devices_arg) == 1
        assert devices_arg[0]["id"] == "adb-A"


# ---------------------------------------------------------------------------
# 11. device_context not modified by scanner
# ---------------------------------------------------------------------------

class TestDeviceContextUnchanged:
    @pytest.mark.asyncio
    async def test_update_detected_does_not_change_context(self):
        from app.main import app as _app  # noqa: F401
        from app.realtime.session_manager import RealtimeSessionManager
        from app.schemas.device_context import DeviceContext

        mgr = RealtimeSessionManager()
        session = mgr.create_session("s1")
        session.device_context = DeviceContext(id="old-device", brand="Apple", model="iPhone 13 Pro")

        await mgr.update_detected_devices("s1", [
            {"id": "adb-NEW", "brand": "Samsung", "model": "Galaxy S24"},
        ])

        assert session.device_context.id == "old-device"
        assert session.device_context.brand == "Apple"
        assert len(session.detected_devices) == 1
        assert session.detected_devices[0].id == "adb-NEW"


# ---------------------------------------------------------------------------
# 12-13. Scanner does not block heartbeat
# ---------------------------------------------------------------------------

class TestScannerNonBlocking:
    @pytest.mark.asyncio
    async def test_scanner_runs_as_background_task(self):
        scanner = DeviceScanner(interval=0.05)

        async def mock_scan(*a):
            return []

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan):
            scanner.start()
            # heartbeat-like work continues
            for _ in range(5):
                await asyncio.sleep(0.02)
            scanner.stop()

        # If we get here, the scanner didn't block


# ---------------------------------------------------------------------------
# 14. ADB error handled without crash
# ---------------------------------------------------------------------------

class TestAdbErrorHandling:
    @pytest.mark.asyncio
    async def test_scan_error_does_not_crash_scanner(self):
        callback = AsyncMock()
        scanner = DeviceScanner(on_change=callback, interval=0.05)

        call_count = 0
        async def mock_scan_error(*a):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("ADB daemon not running")
            return []

        with patch("pc_agent.device_scanner.scan_devices", side_effect=mock_scan_error):
            scanner.start()
            await asyncio.sleep(0.3)
            scanner.stop()

        # Scanner recovered after error — call_count should be > 1
        assert call_count > 1


# ---------------------------------------------------------------------------
# 15-17. Windows no-console flag (V0.6.1)
# ---------------------------------------------------------------------------

class TestNoConsoleFlag:
    def test_subprocess_flags_set_on_windows(self):
        """On Windows, CREATE_NO_WINDOW + SW_HIDE startupinfo must be set."""
        if sys.platform == "win32":
            assert "creationflags" in _SUBPROCESS_FLAGS
            assert _SUBPROCESS_FLAGS["creationflags"] == subprocess.CREATE_NO_WINDOW
            assert "startupinfo" in _SUBPROCESS_FLAGS
            si = _SUBPROCESS_FLAGS["startupinfo"]
            assert si.dwFlags & subprocess.STARTF_USESHOWWINDOW
            assert si.wShowWindow == 0
        else:
            assert _SUBPROCESS_FLAGS == {}

    def test_windows_no_console_helper(self):
        from pc_agent.win_no_console import windows_no_console_kwargs

        flags = windows_no_console_kwargs()
        if sys.platform == "win32":
            assert flags["creationflags"] == subprocess.CREATE_NO_WINDOW
            assert flags["startupinfo"].wShowWindow == 0
        else:
            assert flags == {}

    @pytest.mark.asyncio
    async def test_run_adb_passes_creationflags(self):
        """_run_adb must forward _SUBPROCESS_FLAGS to create_subprocess_exec."""
        captured_kwargs: dict = {}

        async def mock_exec(*args, **kwargs):
            captured_kwargs.update(kwargs)
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"List of devices attached\n\n", b""))
            return proc

        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            await _run_adb("adb", "devices", "-l")

        if sys.platform == "win32":
            assert captured_kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW
            assert "startupinfo" in captured_kwargs
        else:
            assert "creationflags" not in captured_kwargs

    @pytest.mark.asyncio
    async def test_full_scan_uses_no_console(self):
        """scan_devices end-to-end: subprocess must carry no-console flag on Windows."""
        captured_kwargs_list: list[dict] = []

        async def mock_exec(*args, **kwargs):
            captured_kwargs_list.append(dict(kwargs))
            proc = MagicMock()
            proc.returncode = 0
            proc.communicate = AsyncMock(return_value=(b"List of devices attached\n\n", b""))
            return proc

        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            with patch("pc_agent.device_scanner._find_adb", return_value="adb"):
                await scan_devices()

        assert len(captured_kwargs_list) >= 1
        for kw in captured_kwargs_list:
            if sys.platform == "win32":
                assert kw.get("creationflags") == subprocess.CREATE_NO_WINDOW
                assert "startupinfo" in kw
            else:
                assert "creationflags" not in kw
