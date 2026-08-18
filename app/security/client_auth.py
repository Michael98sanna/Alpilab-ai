"""Authorize RepairSession client WebSockets. PC Agent stays on a separate endpoint."""

from __future__ import annotations

import os

from app.pairing.service import PairingService
from app.session.factory import get_session_store, session_store_backend
from app.session.sqlite_store import SQLiteSessionStore

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost", "testclient"})


class ClientAuthError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


def pairing_enforced() -> bool:
    if os.getenv("ALPILAB_REQUIRE_CLIENT_PAIRING", "").strip().lower() in {"1", "true", "yes"}:
        return True
    if os.getenv("ALPILAB_REQUIRE_CLIENT_PAIRING", "").strip().lower() in {"0", "false", "no"}:
        return False
    return session_store_backend() == "sqlite"


def is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    return host.split("%")[0].lower() in LOOPBACK_HOSTS


def is_local_hub_ui(host: str | None, device_type: str) -> bool:
    """Windows embedded UI on loopback does not pair with itself."""
    return is_loopback_host(host) and device_type.strip().lower() == "pc"


def authorize_session_client(
    *,
    host: str | None,
    device_id: str,
    device_type: str,
    pairing_token: str | None,
) -> None:
    if not pairing_enforced():
        return
    if is_local_hub_ui(host, device_type):
        return
    store = get_session_store()
    if not isinstance(store, SQLiteSessionStore):
        raise ClientAuthError("PAIRING_REQUIRED", "Pairing richiesto")
    service = PairingService(store)
    if not pairing_token:
        raise ClientAuthError("PAIRING_REQUIRED", "Pairing richiesto")
    if not service.is_authorized(device_id, pairing_token):
        raise ClientAuthError("UNAUTHORIZED", "Dispositivo non autorizzato")
