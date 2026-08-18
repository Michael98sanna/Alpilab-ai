"""Local Hub HTTP routes — info, pairing, LAN URL."""

from __future__ import annotations

from pydantic import BaseModel

from app.hub.discovery import DEFAULT_HUB_NAME, detect_lan_ip
from app.pairing.service import PairingError, PairingService
from app.session.factory import get_session_store
from app.session.sqlite_store import SQLiteSessionStore


class PairCompleteBody(BaseModel):
    code: str
    client_id: str | None = None
    client_type: str = "phone"
    platform: str = "android"
    device_name: str = "Smartphone"


def _pairing() -> PairingService:
    store = get_session_store()
    if not isinstance(store, SQLiteSessionStore):
        raise PairingError("SQLITE_REQUIRED", "Il pairing richiede SQLite (Local Hub)")
    return PairingService(store)


def hub_info(port: int = 8000) -> dict:
    ip = detect_lan_ip()
    return {
        "name": DEFAULT_HUB_NAME,
        "version": "0.5.0",
        "mode": "local-first",
        "default_session_id": "repair-001",
        "lan_ip": ip,
        "lan_url": f"http://{ip}:{port}",
        "ws_url": f"ws://{ip}:{port}",
        "discovery": "_alpilab._tcp.local.",
        "pairing_required": True,
    }


def start_pairing() -> dict:
    started = _pairing().start()
    info = hub_info()
    return {
        **started,
        "hub_name": info["name"],
        "lan_url": info["lan_url"],
        "qr_payload": {
            "hub": info["lan_url"],
            "ws": info["ws_url"],
            "name": info["name"],
            "code": started["code"],
            "session": "repair-001",
        },
    }


def complete_pairing(body: PairCompleteBody) -> dict:
    return _pairing().complete(
        body.code,
        client_id=body.client_id,
        client_type=body.client_type,
        platform=body.platform,
        device_name=body.device_name,
    )


def list_paired() -> dict:
    return {"clients": _pairing().list_clients()}


def revoke_paired(client_id: str) -> dict:
    _pairing().revoke(client_id)
    return {"status": "revoked", "client_id": client_id}
