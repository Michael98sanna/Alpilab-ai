"""Tests for V0.6 Milestone 3 — Device Selection & Association (backend)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.main import app as _app  # noqa: F401
from app.realtime.events import RealtimeEventType
from app.realtime.session_manager import RealtimeSessionManager
from app.schemas.device_context import DetectedDevice, DeviceContext


def _det(device_id: str, brand: str = "Samsung", model: str = "SM-S931B") -> DetectedDevice:
    return DetectedDevice(
        id=device_id,
        brand=brand,
        model=model,
        serial_number=device_id,
        connection_type="usb",
        source="adb",
        detected_at=datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc),
    )


def _make_mgr() -> RealtimeSessionManager:
    mgr = RealtimeSessionManager()
    mgr.create_session("s1")
    return mgr


# ---------------------------------------------------------------------------
# 1. Zero devices
# ---------------------------------------------------------------------------

class TestZeroDevices:
    @pytest.mark.asyncio
    async def test_empty_detected_list(self):
        mgr = _make_mgr()
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", [])
        session = mgr.get_session("s1")
        assert session.detected_devices == []

    @pytest.mark.asyncio
    async def test_event_emitted_on_clear(self):
        mgr = _make_mgr()
        emitted: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: emitted.append(e))):
            await mgr.update_detected_devices("s1", [])
        assert any(e.event_type == RealtimeEventType.REPAIR_DEVICE_LIST_UPDATED for e in emitted)


# ---------------------------------------------------------------------------
# 2. One device
# ---------------------------------------------------------------------------

class TestOneDevice:
    @pytest.mark.asyncio
    async def test_one_device_stored(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
        session = mgr.get_session("s1")
        assert len(session.detected_devices) == 1
        assert session.detected_devices[0].id == "adb-A"

    @pytest.mark.asyncio
    async def test_list_updated_event_payload(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        events: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: events.append(e))):
            await mgr.update_detected_devices("s1", raw)
        ev = next(e for e in events if e.event_type == RealtimeEventType.REPAIR_DEVICE_LIST_UPDATED)
        assert len(ev.payload["detected_devices"]) == 1


# ---------------------------------------------------------------------------
# 3. Multiple devices
# ---------------------------------------------------------------------------

class TestMultipleDevices:
    @pytest.mark.asyncio
    async def test_all_stored(self):
        mgr = _make_mgr()
        raw = [
            _det("adb-A").model_dump(mode="json"),
            _det("adb-B", brand="Apple", model="iPhone 14").model_dump(mode="json"),
        ]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
        session = mgr.get_session("s1")
        assert len(session.detected_devices) == 2

    @pytest.mark.asyncio
    async def test_ids_correct(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json"), _det("adb-B").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
        ids = {d.id for d in mgr.get_session("s1").detected_devices}
        assert ids == {"adb-A", "adb-B"}


# ---------------------------------------------------------------------------
# 4. Association
# ---------------------------------------------------------------------------

class TestAssociation:
    @pytest.mark.asyncio
    async def test_associate_sets_device_context(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
        session = mgr.get_session("s1")
        assert session.device_context is not None
        assert session.device_context.id == "adb-A"
        assert session.device_context.brand == "Samsung"

    @pytest.mark.asyncio
    async def test_associate_emits_event(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        events: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: events.append(e))):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
        assert any(e.event_type == RealtimeEventType.REPAIR_DEVICE_ASSOCIATED for e in events)

    @pytest.mark.asyncio
    async def test_associate_updates_session_device_label(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
        session = mgr.get_session("s1")
        assert session.device is not None

    @pytest.mark.asyncio
    async def test_associate_unknown_device_raises(self):
        mgr = _make_mgr()
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            with pytest.raises(ValueError, match="not in detected list"):
                await mgr.associate_repair_device("s1", "adb-UNKNOWN")


# ---------------------------------------------------------------------------
# 5. Explicit replacement
# ---------------------------------------------------------------------------

class TestExplicitReplacement:
    @pytest.mark.asyncio
    async def test_reassociate_replaces_context(self):
        mgr = _make_mgr()
        raw = [
            _det("adb-A").model_dump(mode="json"),
            _det("adb-B", brand="Apple", model="iPhone 14").model_dump(mode="json"),
        ]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            assert mgr.get_session("s1").device_context.id == "adb-A"
            await mgr.associate_repair_device("s1", "adb-B")
        assert mgr.get_session("s1").device_context.id == "adb-B"
        assert mgr.get_session("s1").device_context.brand == "Apple"


# ---------------------------------------------------------------------------
# 6. Disassociation
# ---------------------------------------------------------------------------

class TestDisassociation:
    @pytest.mark.asyncio
    async def test_unassociate_clears_context(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            await mgr.unassociate_repair_device("s1")
        assert mgr.get_session("s1").device_context is None

    @pytest.mark.asyncio
    async def test_unassociate_emits_event(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        events: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: events.append(e))):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            await mgr.unassociate_repair_device("s1")
        assert any(e.event_type == RealtimeEventType.REPAIR_DEVICE_UNASSOCIATED for e in events)

    @pytest.mark.asyncio
    async def test_unassociate_does_not_clear_detected_devices(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            await mgr.unassociate_repair_device("s1")
        assert len(mgr.get_session("s1").detected_devices) == 1


# ---------------------------------------------------------------------------
# 7-9. Physical disconnect — device_context preserved
# ---------------------------------------------------------------------------

class TestPhysicalDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_removes_from_detected(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json"), _det("adb-B").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            # Simulate A physically disconnected: B remains
            await mgr.update_detected_devices("s1", [_det("adb-B").model_dump(mode="json")])
        session = mgr.get_session("s1")
        assert len(session.detected_devices) == 1
        assert session.detected_devices[0].id == "adb-B"

    @pytest.mark.asyncio
    async def test_device_context_survives_physical_disconnect(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            # Simulate A disconnected (empty list)
            await mgr.update_detected_devices("s1", [])
        session = mgr.get_session("s1")
        assert session.detected_devices == []
        assert session.device_context is not None
        assert session.device_context.id == "adb-A"

    @pytest.mark.asyncio
    async def test_all_disconnect_context_remains(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            await mgr.update_detected_devices("s1", [])
        assert mgr.get_session("s1").device_context.id == "adb-A"


# ---------------------------------------------------------------------------
# 10-11. Realtime events
# ---------------------------------------------------------------------------

class TestRealtimeEvents:
    @pytest.mark.asyncio
    async def test_association_event_payload(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        events: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: events.append(e))):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A", source_client_device_id="client-1")
        ev = next(e for e in events if e.event_type == RealtimeEventType.REPAIR_DEVICE_ASSOCIATED)
        assert ev.payload["id"] == "adb-A"
        assert ev.source_client_device_id == "client-1"

    @pytest.mark.asyncio
    async def test_unassociation_event_payload(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        events: list[Any] = []
        with patch.object(mgr, "send_event_ws", new=AsyncMock(side_effect=lambda s, e: events.append(e))):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            await mgr.unassociate_repair_device("s1", source_client_device_id="client-2")
        ev = next(e for e in events if e.event_type == RealtimeEventType.REPAIR_DEVICE_UNASSOCIATED)
        assert ev.payload["device_id"] == "adb-A"
        assert ev.source_client_device_id == "client-2"


# ---------------------------------------------------------------------------
# 12. inbound WS message routing
# ---------------------------------------------------------------------------

class TestInboundMessageRouting:
    @pytest.mark.asyncio
    async def test_associate_via_client_message(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            result = await mgr.handle_client_message(
                "s1", "dev-client",
                {"type": "associate_repair_device", "repair_device_id": "adb-A"},
            )
        assert result == "ack"
        assert mgr.get_session("s1").device_context.id == "adb-A"

    @pytest.mark.asyncio
    async def test_unassociate_via_client_message(self):
        mgr = _make_mgr()
        raw = [_det("adb-A").model_dump(mode="json")]
        with patch.object(mgr, "send_event_ws", new=AsyncMock()):
            await mgr.update_detected_devices("s1", raw)
            await mgr.associate_repair_device("s1", "adb-A")
            result = await mgr.handle_client_message(
                "s1", "dev-client",
                {"type": "unassociate_repair_device"},
            )
        assert result == "ack"
        assert mgr.get_session("s1").device_context is None
