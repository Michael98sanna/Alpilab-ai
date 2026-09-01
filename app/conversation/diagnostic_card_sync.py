"""Sync chat messages to persistent diagnostic cards."""

from __future__ import annotations

import logging
from typing import Any

from app.models.database import SessionLocal
from app.realtime.session_state import RealtimeSessionData
from app.services.diagnostic_card_service import DiagnosticCardService

logger = logging.getLogger(__name__)


def _resolve_repair_device_id(
    session: RealtimeSessionData | None,
    fallback_device_id: str,
) -> str:
    if session and session.device_context:
        return session.device_context.id
    return fallback_device_id


def _resolve_device_name(session: RealtimeSessionData | None, device_id: str) -> str:
    if session is None:
        return device_id
    if session.device_context and session.device_context.id == device_id:
        return session.device_context.display_name
    connected = session.devices.get(device_id)
    if connected:
        return connected.device_name
    if session.device and session.device == device_id:
        return session.device
    return device_id


def record_user_message(
    session_id: str,
    device_id: str,
    text: str,
    *,
    session: RealtimeSessionData | None = None,
) -> str | None:
    """Persist user message on the diagnostic card for this session/device."""
    repair_device_id = _resolve_repair_device_id(session, device_id)
    db = SessionLocal()
    try:
        service = DiagnosticCardService(db)
        card = service.get_or_create_card(
            session_id=session_id,
            device_id=repair_device_id,
            device_name=_resolve_device_name(session, repair_device_id),
        )
        service.add_message(card.id, "user", text)
        if session and session.issue and not card.current_symptom:
            service.update_card_state(card.id, {"current_symptom": session.issue})
        return card.id
    except Exception:
        logger.exception(
            "Failed to persist user message session=%s device=%s",
            session_id,
            device_id,
        )
        return None
    finally:
        db.close()


def record_assistant_message(
    card_id: str | None,
    content: str,
    *,
    findings: dict[str, Any] | None = None,
    session_id: str | None = None,
    device_id: str | None = None,
    session: RealtimeSessionData | None = None,
) -> None:
    """Persist assistant reply and optional diagnostic findings."""
    if not content.strip():
        return
    db = SessionLocal()
    try:
        service = DiagnosticCardService(db)
        resolved_card_id = card_id
        if not resolved_card_id and session_id and device_id:
            repair_device_id = _resolve_repair_device_id(session, device_id)
            card = service.get_card_by_session_and_device(session_id, repair_device_id)
            resolved_card_id = card.id if card else None
        if not resolved_card_id:
            return
        service.add_message(resolved_card_id, "assistant", content)
        if findings:
            updates: dict[str, Any] = {}
            if findings.get("hypothesis") is not None:
                updates["hypothesis"] = findings["hypothesis"]
            if findings.get("confidence") is not None:
                updates["confidence"] = findings["confidence"]
            if findings.get("diagnostic_stage") is not None:
                updates["diagnostic_stage"] = findings["diagnostic_stage"]
            if updates:
                service.update_card_state(resolved_card_id, updates)
    except Exception:
        logger.exception("Failed to persist assistant message card=%s", card_id)
    finally:
        db.close()
