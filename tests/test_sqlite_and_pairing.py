"""SQLite session store and realtime snapshot persistence."""

from pathlib import Path

from app.realtime.persistence import persistable_snapshot, snapshot_dict_to_session
from app.realtime.session_manager import RealtimeSessionManager
from app.realtime.session_state import new_session
from app.schemas.session import (
    ClientDevice,
    RepairSessionContext,
    SessionParticipant,
    User,
)
from app.session.sqlite_store import SQLiteSessionStore
from app.pairing.service import PairingError, PairingService


def test_sqlite_context_survives_reopen(tmp_path: Path) -> None:
    db = tmp_path / "alpilab.db"
    store = SQLiteSessionStore(db)
    store.save_user(User(id="u1", display_name="Tech"))
    store.save_context(RepairSessionContext(repair_session_id="repair-001"))
    store.close()

    store2 = SQLiteSessionStore(db)
    loaded = store2.get_context("repair-001")
    assert loaded is not None
    assert loaded.repair_session_id == "repair-001"
    store2.close()


def test_sqlite_participant_and_resume(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "s.db")
    store.save_user(User(id="u1", display_name="Tech"))
    store.save_client_device(ClientDevice(id="pc-1", user_id="u1", label="PC"))
    store.save_context(RepairSessionContext(repair_session_id="repair-001"))
    store.add_participant(
        SessionParticipant(
            id="p1",
            repair_session_id="repair-001",
            client_device_id="pc-1",
            user_id="u1",
        )
    )
    parts = store.participants_for_session("repair-001")
    assert len(parts) == 1
    assert store.recent_contexts()[0].repair_session_id == "repair-001"


def test_realtime_snapshot_roundtrip(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "rt.db")
    session = new_session("repair-001")
    session.device = "iPhone 13"
    payload = persistable_snapshot(session)
    store.save_realtime_snapshot("repair-001", payload)

    restored = snapshot_dict_to_session(store.load_realtime_snapshot("repair-001"))
    assert restored.session_id == "repair-001"
    assert restored.device == "iPhone 13"

    manager = RealtimeSessionManager()
    manager.attach_persistence(store)
    loaded = manager.get_session("repair-001")
    assert loaded is not None
    assert loaded.device == "iPhone 13"


async def test_persist_on_chat(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "chat.db")
    manager = RealtimeSessionManager()
    manager.attach_persistence(store)
    manager.create_session("repair-001")
    await manager.add_chat_message("repair-001", "pc-1", "Ciao", role="user")
    snap = store.load_realtime_snapshot("repair-001")
    assert snap is not None
    assert any(m["content"] == "Ciao" for m in snap["conversation"])


def test_pairing_flow(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "pair.db")
    svc = PairingService(store)
    started = svc.start()
    result = svc.complete(
        started["code"],
        client_id="phone-1",
        client_type="phone",
        platform="android",
        device_name="Pixel",
    )
    assert result["status"] == "authorized"
    assert svc.is_authorized("phone-1", result["token"])
    clients = svc.list_clients()
    assert clients[0]["device_name"] == "Pixel"
    svc.revoke("phone-1")
    assert not svc.is_authorized("phone-1", result["token"])


def test_pairing_rejects_bad_code(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "pair2.db")
    svc = PairingService(store)
    try:
        svc.complete("000000", client_id=None, client_type="phone", platform="android", device_name="X")
        raise AssertionError("should fail")
    except PairingError as exc:
        assert exc.code == "INVALID_PAIRING_CODE"
