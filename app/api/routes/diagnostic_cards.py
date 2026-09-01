"""REST endpoints for diagnostic card persistence."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.diagnostic_card import (
    DiagnosticCardArchive,
    DiagnosticCardCreate,
    DiagnosticCardUpdate,
    DiagnosticMessageCreate,
)
from app.services.diagnostic_card_service import DiagnosticCardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diagnostic-cards", tags=["Diagnostic Cards"])


def _card_payload(card) -> dict:
    return {
        "id": card.id,
        "session_id": card.session_id,
        "device_id": card.device_id,
        "device_name": card.device_name,
        "status": card.status,
        "created_at": card.created_at.isoformat(),
        "updated_at": card.updated_at.isoformat(),
        "current_symptom": card.current_symptom,
        "hypothesis": card.hypothesis,
        "confidence": card.confidence,
        "diagnostic_stage": card.diagnostic_stage,
    }


@router.get("")
def list_active_cards(
    session_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Lista tutte le schede diagnostiche attive."""
    service = DiagnosticCardService(db)
    cards = service.get_active_cards(session_id=session_id)
    return {
        "count": len(cards),
        "cards": [_card_payload(card) for card in cards],
    }


@router.post("")
def create_card(
    body: DiagnosticCardCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Crea nuova scheda diagnostica."""
    service = DiagnosticCardService(db)
    existing = service.get_card_by_session_and_device(body.session_id, body.device_id)
    if existing:
        return {
            "id": existing.id,
            "session_id": existing.session_id,
            "status": "existing",
        }
    card = service.create_card(body.device_id, body.device_name, body.session_id)
    return {
        "id": card.id,
        "session_id": card.session_id,
        "status": "created",
    }


@router.get("/{card_id}")
def get_card(card_id: str, db: Session = Depends(get_db)) -> dict:
    """Carica scheda completa con storico."""
    service = DiagnosticCardService(db)
    card = service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {
        "card": _card_payload(card),
        "conversation": service.get_conversation_history(card_id),
        "summary": service.get_quick_summary(card_id),
    }


@router.get("/{card_id}/summary")
def get_card_summary(card_id: str, db: Session = Depends(get_db)) -> dict:
    """Riassunto rapido della scheda."""
    service = DiagnosticCardService(db)
    summary = service.get_quick_summary(card_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Card not found")
    return summary


@router.patch("/{card_id}")
def update_card(
    card_id: str,
    updates: DiagnosticCardUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """Aggiorna stato della scheda."""
    service = DiagnosticCardService(db)
    card = service.update_card_state(
        card_id,
        updates.model_dump(exclude_unset=True),
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"status": "updated", "card_id": card_id}


@router.post("/{card_id}/archive")
def archive_card(
    card_id: str,
    body: DiagnosticCardArchive,
    db: Session = Depends(get_db),
) -> dict:
    """Archivia scheda e prepara indexing knowledge base."""
    service = DiagnosticCardService(db)
    card = service.archive_card(
        card_id,
        body.outcome,
        body.final_diagnosis,
        body.solution,
    )
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    service.index_in_knowledge_base(card_id)
    return {
        "status": "archived",
        "card_id": card_id,
        "outcome": body.outcome,
    }


@router.get("/{card_id}/messages")
def get_messages(card_id: str, db: Session = Depends(get_db)) -> dict:
    """Storico messaggi completo."""
    service = DiagnosticCardService(db)
    card = service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"messages": service.get_conversation_history(card_id)}


@router.post("/{card_id}/message")
def add_message(
    card_id: str,
    body: DiagnosticMessageCreate,
    db: Session = Depends(get_db),
) -> dict:
    """Aggiungi messaggio alla conversazione."""
    service = DiagnosticCardService(db)
    card = service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    service.add_message(card_id, body.role, body.content)
    return {"status": "added", "card_id": card_id}
