"""Tests for V0.6 Device Context — Milestone 1."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.main import app as _app  # noqa: F401 — resolve circular imports
from app.realtime.events import RealtimeEventType
from app.realtime.session_manager import RealtimeSessionManager
from app.realtime.session_state import new_session
from app.realtime.persistence import persistable_snapshot, snapshot_dict_to_session
from app.schemas.device_context import DetectedDevice, DeviceContext
from app.schemas.repair import RepairSession


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sample_detected(device_id: str = "det-001", **overrides) -> DetectedDevice:
    defaults = dict(
        id=device_id,
        brand="Samsung",
        model="SM-S931B",
        serial_number="RFCY11GRHTZ",
        imei="123456789012345",
        connection_type="usb",
        source="adb",
        detected_at=datetime(2026, 8, 19, 10, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return DetectedDevice(**defaults)


def _sample_detected_iphone(device_id: str = "det-002") -> DetectedDevice:
    return DetectedDevice(
        id=device_id,
        brand="Apple",
        model="iPhone 13 Pro",
        source="3utools",
        connection_type="usb",
    )


# ---------------------------------------------------------------------------
# 1. RepairSession without device
# ---------------------------------------------------------------------------

class TestRepairSessionDeviceOptional:
    def test_session_without_device(self):
        s = RepairSession(id="s1")
        assert s.device_id is None

    def test_session_with_device(self):
        s = RepairSession(id="s1", device_id="d1")
        assert s.device_id == "d1"

    def test_backward_compat_existing_session(self):
        data = {"id": "s1", "device_id": "d1", "status": "open"}
        s = RepairSession.model_validate(data)
        assert s.device_id == "d1"

    def test_backward_compat_missing_device_id(self):
        data = {"id": "s1", "status": "open"}
        s = RepairSession.model_validate(data)
        assert s.device_id is None


# ---------------------------------------------------------------------------
# 2. DeviceContext & DetectedDevice schemas
# ---------------------------------------------------------------------------

class TestDeviceContextSchema:
    def test_detected_display_name(self):
        d = _sample_detected()
        assert d.display_name == "Samsung SM-S931B"

    def test_detected_display_name_fallback(self):
        d = DetectedDevice(id="x")
        assert d.display_name == "x"

    def test_from_detected(self):
        det = _sample_detected()
        now = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
        ctx = DeviceContext.from_detected(det, associated_at=now)
        assert ctx.id == det.id
        assert ctx.brand == "Samsung"
        assert ctx.model == "SM-S931B"
        assert ctx.imei == "123456789012345"
        assert ctx.associated_at == now
        assert ctx.source == "adb"

    def test_device_context_serialization(self):
        ctx = DeviceContext(id="c1", brand="Apple", model="iPhone 13 Pro")
        data = ctx.model_dump(mode="json")
        restored = DeviceContext.model_validate(data)
        assert restored.brand == "Apple"
        assert restored.model == "iPhone 13 Pro"
        assert restored.storage is None


# ---------------------------------------------------------------------------
# 3-4. Snapshot with/without device_context
# ---------------------------------------------------------------------------

class TestSnapshotDeviceContext:
    def test_snapshot_without_device_context(self):
        session = new_session("s1")
        snap = session.snapshot()
        assert snap.device_context is None
        assert snap.detected_devices == []

    def test_snapshot_with_device_context(self):
        session = new_session("s1")
        det = _sample_detected()
        session.device_context = DeviceContext.from_detected(det)
        session.detected_devices = [det]
        snap = session.snapshot()
        assert snap.device_context is not None
        assert snap.device_context["brand"] == "Samsung"
        assert len(snap.detected_devices) == 1

    def test_backward_compat_old_snapshot_no_device_fields(self):
        """Old snapshots without device_context/detected_devices load fine."""
        old_payload = {
            "session": {"id": "s1", "label": "Repair", "status": "active", "diagnosis_label": ""},
            "participants": [],
            "conversation": [],
            "repair_context": {"id": "s1", "label": "Repair", "status": "active", "diagnosis_label": ""},
            "diagnostic_state": [],
            "assistant_status": "IDLE",
            "state_version": 3,
        }
        session = snapshot_dict_to_session(old_payload)
        assert session.device_context is None
        assert session.detected_devices == []
        assert session.state_version == 3


# ---------------------------------------------------------------------------
# 5-7. Detected devices: 0, 1, N
# ---------------------------------------------------------------------------

class TestDetectedDevices:
    def test_zero_detected(self):
        session = new_session("s1")
        assert session.detected_devices == []

    def test_one_detected(self):
        session = new_session("s1")
        session.detected_devices = [_sample_detected()]
        assert len(session.detected_devices) == 1
        assert session.detected_devices[0].brand == "Samsung"

    def test_n_detected(self):
        session = new_session("s1")
        session.detected_devices = [_sample_detected(), _sample_detected_iphone()]
        assert len(session.detected_devices) == 2
        names = {d.display_name for d in session.detected_devices}
        assert names == {"Samsung SM-S931B", "Apple iPhone 13 Pro"}


# ---------------------------------------------------------------------------
# 8-10. Association, replacement, unassociation
# ---------------------------------------------------------------------------

class TestAssociation:
    @pytest.fixture()
    def manager(self):
        return RealtimeSessionManager()

    @pytest.mark.asyncio
    async def test_associate(self, manager):
        session = manager.create_session("s1")
        session.detected_devices = [_sample_detected()]
        await manager.associate_repair_device("s1", "det-001")
        assert session.device_context is not None
        assert session.device_context.brand == "Samsung"
        assert session.device == "Samsung SM-S931B"
        assert session.device_context.associated_at is not None

    @pytest.mark.asyncio
    async def test_associate_unknown_device_raises(self, manager):
        manager.create_session("s1")
        with pytest.raises(ValueError, match="not in detected"):
            await manager.associate_repair_device("s1", "nonexistent")

    @pytest.mark.asyncio
    async def test_replace_association(self, manager):
        session = manager.create_session("s1")
        session.detected_devices = [_sample_detected(), _sample_detected_iphone()]
        await manager.associate_repair_device("s1", "det-001")
        assert session.device_context.brand == "Samsung"
        await manager.associate_repair_device("s1", "det-002")
        assert session.device_context.brand == "Apple"
        assert session.device == "Apple iPhone 13 Pro"

    @pytest.mark.asyncio
    async def test_unassociate(self, manager):
        session = manager.create_session("s1")
        session.detected_devices = [_sample_detected()]
        await manager.associate_repair_device("s1", "det-001")
        assert session.device_context is not None
        await manager.unassociate_repair_device("s1")
        assert session.device_context is None
        assert session.device is None

    @pytest.mark.asyncio
    async def test_unassociate_when_none(self, manager):
        manager.create_session("s1")
        await manager.unassociate_repair_device("s1")


# ---------------------------------------------------------------------------
# 11. Persistence round-trip
# ---------------------------------------------------------------------------

class TestPersistenceRoundTrip:
    def test_persist_and_restore_with_device_context(self):
        session = new_session("s1")
        det = _sample_detected()
        session.device_context = DeviceContext.from_detected(
            det, associated_at=datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
        )
        session.detected_devices = [det, _sample_detected_iphone()]

        payload = persistable_snapshot(session)
        restored = snapshot_dict_to_session(payload)

        assert restored.device_context is not None
        assert restored.device_context.brand == "Samsung"
        assert restored.device_context.imei == "123456789012345"
        assert len(restored.detected_devices) == 2

    def test_persist_and_restore_without_device_context(self):
        session = new_session("s1")
        payload = persistable_snapshot(session)
        restored = snapshot_dict_to_session(payload)
        assert restored.device_context is None
        assert restored.detected_devices == []


# ---------------------------------------------------------------------------
# 12. Realtime events exist
# ---------------------------------------------------------------------------

class TestRealtimeEvents:
    def test_repair_device_events_exist(self):
        assert RealtimeEventType.REPAIR_DEVICE_DETECTED.value == "REPAIR_DEVICE_DETECTED"
        assert RealtimeEventType.REPAIR_DEVICE_LIST_UPDATED.value == "REPAIR_DEVICE_LIST_UPDATED"
        assert RealtimeEventType.REPAIR_DEVICE_ASSOCIATED.value == "REPAIR_DEVICE_ASSOCIATED"
        assert RealtimeEventType.REPAIR_DEVICE_UNASSOCIATED.value == "REPAIR_DEVICE_UNASSOCIATED"
        assert RealtimeEventType.REPAIR_DEVICE_DISCONNECTED.value == "REPAIR_DEVICE_DISCONNECTED"

    def test_existing_device_events_unchanged(self):
        assert RealtimeEventType.DEVICE_CONNECTED.value == "DEVICE_CONNECTED"
        assert RealtimeEventType.DEVICE_DISCONNECTED.value == "DEVICE_DISCONNECTED"
        assert RealtimeEventType.DEVICE_HEARTBEAT.value == "DEVICE_HEARTBEAT"


# ---------------------------------------------------------------------------
# 13. update_detected_devices manager method
# ---------------------------------------------------------------------------

class TestUpdateDetectedDevices:
    @pytest.fixture()
    def manager(self):
        return RealtimeSessionManager()

    @pytest.mark.asyncio
    async def test_update_detected_list(self, manager):
        session = manager.create_session("s1")
        devices = [
            {"id": "d1", "brand": "Samsung", "model": "A52"},
            {"id": "d2", "brand": "Apple", "model": "iPhone 14"},
        ]
        await manager.update_detected_devices("s1", devices)
        assert len(session.detected_devices) == 2
        assert session.detected_devices[0].brand == "Samsung"
        assert session.detected_devices[1].brand == "Apple"

    @pytest.mark.asyncio
    async def test_update_detected_replaces(self, manager):
        session = manager.create_session("s1")
        await manager.update_detected_devices("s1", [{"id": "d1", "brand": "Samsung", "model": "A52"}])
        assert len(session.detected_devices) == 1
        await manager.update_detected_devices("s1", [])
        assert len(session.detected_devices) == 0


# ---------------------------------------------------------------------------
# 14. Client inbound messages
# ---------------------------------------------------------------------------

class TestClientInboundDeviceMessages:
    @pytest.fixture()
    def manager(self):
        return RealtimeSessionManager()

    @pytest.mark.asyncio
    async def test_associate_via_client_message(self, manager):
        session = manager.create_session("s1")
        session.detected_devices = [_sample_detected()]
        result = await manager.handle_client_message("s1", "pc-1", {
            "type": "associate_repair_device",
            "repair_device_id": "det-001",
        })
        assert result == "ack"
        assert session.device_context is not None
        assert session.device_context.id == "det-001"

    @pytest.mark.asyncio
    async def test_unassociate_via_client_message(self, manager):
        session = manager.create_session("s1")
        session.detected_devices = [_sample_detected()]
        await manager.associate_repair_device("s1", "det-001")
        result = await manager.handle_client_message("s1", "pc-1", {
            "type": "unassociate_repair_device",
        })
        assert result == "ack"
        assert session.device_context is None
