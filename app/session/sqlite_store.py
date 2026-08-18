"""SQLite-backed session persistence — local-first, no cloud."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.session import (
    ClientDevice,
    RepairSessionContext,
    SessionParticipant,
    User,
)
from app.schemas.session_events import SessionEvent

DEFAULT_DB_PATH = Path("data") / "alpilab.db"


def _utc(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


class SQLiteSessionStore:
    """Local persistence store. Survives Local Hub restart."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        path = Path(db_path) if db_path else DEFAULT_DB_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        self._conn.close()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS client_devices (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contexts (
                repair_session_id TEXT PRIMARY KEY,
                last_activity_at TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                repair_session_id TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_events (
                id TEXT PRIMARY KEY,
                repair_session_id TEXT,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS realtime_snapshots (
                session_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pairing_challenges (
                code TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS paired_clients (
                client_id TEXT PRIMARY KEY,
                client_type TEXT NOT NULL,
                platform TEXT NOT NULL,
                device_name TEXT NOT NULL,
                token TEXT NOT NULL,
                status TEXT NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                paired_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def save_user(self, user: User) -> User:
        self._conn.execute(
            "INSERT OR REPLACE INTO users (id, payload) VALUES (?, ?)",
            (user.id, user.model_dump_json()),
        )
        self._conn.commit()
        return user

    def save_client_device(self, device: ClientDevice) -> ClientDevice:
        self._conn.execute(
            "INSERT OR REPLACE INTO client_devices (id, user_id, payload) VALUES (?, ?, ?)",
            (device.id, device.user_id, device.model_dump_json()),
        )
        self._conn.commit()
        return device

    def save_context(self, context: RepairSessionContext) -> RepairSessionContext:
        context.last_activity_at = datetime.now(timezone.utc)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO contexts (repair_session_id, last_activity_at, payload)
            VALUES (?, ?, ?)
            """,
            (
                context.repair_session_id,
                _iso(context.last_activity_at),
                context.model_dump_json(),
            ),
        )
        self._conn.commit()
        return context

    def get_context(self, repair_session_id: str) -> RepairSessionContext | None:
        row = self._conn.execute(
            "SELECT payload FROM contexts WHERE repair_session_id = ?",
            (repair_session_id,),
        ).fetchone()
        if row is None:
            return None
        return RepairSessionContext.model_validate_json(row["payload"])

    def add_participant(self, participant: SessionParticipant) -> SessionParticipant:
        self._conn.execute(
            "INSERT OR REPLACE INTO participants (id, repair_session_id, payload) VALUES (?, ?, ?)",
            (participant.id, participant.repair_session_id, participant.model_dump_json()),
        )
        self._conn.commit()
        context = self.get_context(participant.repair_session_id)
        if context is not None:
            if participant.id not in context.active_participant_ids:
                context.active_participant_ids.append(participant.id)
            context.last_active_client_device_id = participant.client_device_id
            self.save_context(context)
        return participant

    def participants_for_session(self, repair_session_id: str) -> list[SessionParticipant]:
        rows = self._conn.execute(
            "SELECT payload FROM participants WHERE repair_session_id = ?",
            (repair_session_id,),
        ).fetchall()
        items = [SessionParticipant.model_validate_json(r["payload"]) for r in rows]
        return [p for p in items if p.is_active]

    def client_devices_for_user(self, user_id: str) -> list[ClientDevice]:
        rows = self._conn.execute(
            "SELECT payload FROM client_devices WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [ClientDevice.model_validate_json(r["payload"]) for r in rows]

    def active_contexts_for_user(self, user_id: str) -> list[RepairSessionContext]:
        user_device_ids = {d.id for d in self.client_devices_for_user(user_id)}
        rows = self._conn.execute("SELECT payload FROM participants").fetchall()
        session_ids = {
            SessionParticipant.model_validate_json(r["payload"]).repair_session_id
            for r in rows
            if SessionParticipant.model_validate_json(r["payload"]).client_device_id
            in user_device_ids
            and SessionParticipant.model_validate_json(r["payload"]).is_active
        }
        return [c for sid in session_ids if (c := self.get_context(sid)) is not None]

    def append_event(self, event: SessionEvent) -> SessionEvent:
        self._conn.execute(
            "INSERT OR REPLACE INTO session_events (id, repair_session_id, payload) VALUES (?, ?, ?)",
            (event.id, event.repair_session_id, event.model_dump_json()),
        )
        self._conn.commit()
        return event

    def recent_contexts(self, limit: int = 10) -> list[RepairSessionContext]:
        rows = self._conn.execute(
            """
            SELECT payload FROM contexts
            ORDER BY last_activity_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [RepairSessionContext.model_validate_json(r["payload"]) for r in rows]

    def save_realtime_snapshot(self, session_id: str, payload: dict) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO realtime_snapshots (session_id, payload, updated_at)
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                json.dumps(payload),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def load_realtime_snapshot(self, session_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT payload FROM realtime_snapshots WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def list_realtime_session_ids(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT session_id FROM realtime_snapshots ORDER BY updated_at DESC"
        ).fetchall()
        return [r["session_id"] for r in rows]

    def create_pairing_challenge(self, code: str, expires_at: datetime) -> None:
        now = datetime.now(timezone.utc)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO pairing_challenges (code, created_at, expires_at, consumed)
            VALUES (?, ?, ?, 0)
            """,
            (code, now.isoformat(), expires_at.isoformat()),
        )
        self._conn.commit()

    def consume_pairing_challenge(self, code: str) -> bool:
        row = self._conn.execute(
            "SELECT expires_at, consumed FROM pairing_challenges WHERE code = ?",
            (code,),
        ).fetchone()
        if row is None or row["consumed"]:
            return False
        expires = _utc(row["expires_at"])
        if expires is None or expires < datetime.now(timezone.utc):
            return False
        self._conn.execute(
            "UPDATE pairing_challenges SET consumed = 1 WHERE code = ?",
            (code,),
        )
        self._conn.commit()
        return True

    def save_paired_client(
        self,
        client_id: str,
        client_type: str,
        platform: str,
        device_name: str,
        token: str,
        status: str = "authorized",
    ) -> None:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO paired_clients
            (client_id, client_type, platform, device_name, token, status, revoked, paired_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                client_id,
                client_type,
                platform,
                device_name,
                token,
                status,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def get_paired_client(self, client_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT * FROM paired_clients WHERE client_id = ?",
            (client_id,),
        ).fetchone()
        return dict(row) if row else None

    def list_paired_clients(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM paired_clients ORDER BY paired_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def revoke_paired_client(self, client_id: str) -> bool:
        cur = self._conn.execute(
            "UPDATE paired_clients SET revoked = 1, status = 'revoked' WHERE client_id = ?",
            (client_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0
