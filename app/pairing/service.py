"""LAN pairing: PC shows code/QR, mobile authorizes."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.session.sqlite_store import SQLiteSessionStore

DEFAULT_TTL_SECONDS = 300


class PairingError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class PairingService:
    def __init__(self, store: SQLiteSessionStore, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._store = store
        self._ttl = ttl_seconds

    def start(self) -> dict:
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires = datetime.now(timezone.utc) + timedelta(seconds=self._ttl)
        self._store.create_pairing_challenge(code, expires)
        return {
            "code": code,
            "expires_at": expires.isoformat(),
            "ttl_seconds": self._ttl,
        }

    def complete(
        self,
        code: str,
        *,
        client_id: str | None,
        client_type: str,
        platform: str,
        device_name: str,
    ) -> dict:
        if not self._store.consume_pairing_challenge(code.strip()):
            raise PairingError("INVALID_PAIRING_CODE", "Codice pairing non valido o scaduto")
        cid = client_id or f"client-{uuid4().hex[:10]}"
        token = secrets.token_urlsafe(24)
        self._store.save_paired_client(
            client_id=cid,
            client_type=client_type or "phone",
            platform=platform or "unknown",
            device_name=device_name or "Device",
            token=token,
            status="authorized",
        )
        return {
            "client_id": cid,
            "client_type": client_type,
            "platform": platform,
            "device_name": device_name,
            "status": "authorized",
            "revoked": False,
            "token": token,
        }

    def list_clients(self) -> list[dict]:
        clients = []
        for row in self._store.list_paired_clients():
            clients.append(
                {
                    "client_id": row["client_id"],
                    "client_type": row["client_type"],
                    "platform": row["platform"],
                    "device_name": row["device_name"],
                    "status": row["status"],
                    "revoked": bool(row["revoked"]),
                    "paired_at": row["paired_at"],
                }
            )
        return clients

    def revoke(self, client_id: str) -> None:
        if not self._store.revoke_paired_client(client_id):
            raise PairingError("CLIENT_NOT_FOUND", "Dispositivo non trovato")

    def is_authorized(self, client_id: str, token: str | None) -> bool:
        row = self._store.get_paired_client(client_id)
        if row is None or row["revoked"]:
            return False
        if not token or row["token"] != token:
            return False
        return True
