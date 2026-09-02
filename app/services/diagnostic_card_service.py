"""Lifecycle management for persistent diagnostic repair cards."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.knowledge.knowledge_base import KnowledgeBase
from app.knowledge.records import RepairKnowledgeRecord
from app.models.orm_models import (
    ArchivedDiagnosticCard,
    DiagnosticCard,
    DiagnosticMessage,
)

logger = logging.getLogger(__name__)


class DiagnosticCardService:
    """Gestisce ciclo vita schede diagnostiche."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_card(
        self,
        device_id: str,
        device_name: str,
        session_id: str,
    ) -> DiagnosticCard:
        """Crea nuova scheda diagnostica."""
        card = DiagnosticCard(
            id=str(uuid.uuid4()),
            session_id=session_id,
            device_id=device_id,
            device_name=device_name,
            status="active",
            test_results={},
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        logger.info("Created diagnostic card %s for %s", card.id, device_name)
        return card

    def get_active_cards(self, session_id: str | None = None) -> list[DiagnosticCard]:
        """Ritorna tutte le schede attive, opzionalmente filtrate per sessione."""
        query = self.db.query(DiagnosticCard).filter(DiagnosticCard.status == "active")
        if session_id:
            query = query.filter(DiagnosticCard.session_id == session_id)
        return query.order_by(DiagnosticCard.updated_at.desc()).all()

    def get_card(self, card_id: str) -> DiagnosticCard | None:
        """Carica una scheda."""
        return (
            self.db.query(DiagnosticCard)
            .filter(DiagnosticCard.id == card_id)
            .first()
        )

    def get_card_by_session(self, session_id: str) -> DiagnosticCard | None:
        """Carica la scheda attiva più recente per session_id."""
        return (
            self.db.query(DiagnosticCard)
            .filter(
                DiagnosticCard.session_id == session_id,
                DiagnosticCard.status == "active",
            )
            .order_by(DiagnosticCard.updated_at.desc())
            .first()
        )

    def get_card_by_session_and_device(
        self,
        session_id: str,
        device_id: str,
    ) -> DiagnosticCard | None:
        """Carica scheda attiva per sessione e device."""
        return (
            self.db.query(DiagnosticCard)
            .filter(
                DiagnosticCard.session_id == session_id,
                DiagnosticCard.device_id == device_id,
                DiagnosticCard.status == "active",
            )
            .order_by(DiagnosticCard.updated_at.desc())
            .first()
        )

    def get_or_create_card(
        self,
        session_id: str,
        device_id: str,
        device_name: str,
    ) -> DiagnosticCard:
        """Restituisce scheda esistente o ne crea una nuova."""
        card = self.get_card_by_session_and_device(session_id, device_id)
        if card:
            return card
        return self.create_card(device_id, device_name, session_id)

    def add_message(
        self,
        card_id: str,
        role: str,
        content: str,
        tool_calls: dict[str, Any] | None = None,
    ) -> None:
        """Aggiungi messaggio alla conversazione."""
        message = DiagnosticMessage(
            id=str(uuid.uuid4()),
            card_id=card_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )
        self.db.add(message)
        card = self.get_card(card_id)
        if card:
            card.updated_at = datetime.now(UTC)
        self.db.commit()

    def get_conversation_history(self, card_id: str) -> list[dict[str, str]]:
        """Carica storico conversazione."""
        messages = (
            self.db.query(DiagnosticMessage)
            .filter(DiagnosticMessage.card_id == card_id)
            .order_by(DiagnosticMessage.created_at)
            .all()
        )
        return [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "tool_calls": message.tool_calls,
            }
            for message in messages
        ]

    def update_card_state(
        self,
        card_id: str,
        updates: dict[str, Any],
    ) -> DiagnosticCard | None:
        """Aggiorna stato diagnostico."""
        card = self.get_card(card_id)
        if not card:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(card, key):
                setattr(card, key, value)
        card.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(card)
        return card

    def get_quick_summary(self, card_id: str) -> dict[str, Any] | None:
        """Riassunto rapido della scheda."""
        card = self.get_card(card_id)
        if not card:
            return None
        messages_count = (
            self.db.query(DiagnosticMessage)
            .filter(DiagnosticMessage.card_id == card_id)
            .count()
        )
        return {
            "device": card.device_name,
            "status": card.status,
            "started": card.created_at.isoformat(),
            "updated": card.updated_at.isoformat(),
            "current_symptom": card.current_symptom,
            "hypothesis": card.hypothesis,
            "confidence": card.confidence,
            "messages_count": messages_count,
            "diagnostic_stage": card.diagnostic_stage,
        }

    def archive_card(
        self,
        card_id: str,
        outcome: str,
        final_diagnosis: str,
        solution: str,
    ) -> DiagnosticCard | None:
        """Archivia scheda e prepara per knowledge base."""
        card = self.get_card(card_id)
        if not card:
            return None
        card.status = "archived"
        card.archived_at = datetime.now(UTC)
        card.outcome = outcome
        card.final_diagnosis = final_diagnosis
        card.solution_applied = solution
        self.db.commit()

        archived = ArchivedDiagnosticCard(
            id=str(uuid.uuid4()),
            original_card_id=card_id,
            device_id=card.device_id,
            symptoms=card.current_symptom or "",
            diagnosis=final_diagnosis,
            solution=solution,
            outcome=outcome,
            confidence=card.confidence,
        )
        self.db.add(archived)
        self.db.commit()
        self.db.refresh(card)
        logger.info("Archived card %s outcome=%s", card_id, outcome)
        return card

    def index_in_knowledge_base(self, card_id: str) -> bool:
        """Indexa scheda archiviata nel knowledge base (per RAG future)."""
        try:
            archived = (
                self.db.query(ArchivedDiagnosticCard)
                .filter(ArchivedDiagnosticCard.original_card_id == card_id)
                .first()
            )
            if not archived:
                return False

            card = self.get_card(card_id)
            if not card:
                return False

            symptoms = [archived.symptoms] if archived.symptoms else []
            record = RepairKnowledgeRecord(
                session_id=card_id,
                device_model=card.device_id,
                device_brand=card.device_name,
                symptoms=symptoms,
                diagnosis=archived.diagnosis,
                solution=archived.solution,
                technical_notes=f"Outcome: {archived.outcome}",
                status="completed" if archived.outcome == "success" else "failed",
            )
            KnowledgeBase(self.db).index_repair(record)
            archived.indexed_in_kb = True
            self.db.commit()
            logger.info("Indexed in KB: %s", card_id)
            return True
        except Exception:
            logger.exception("Error indexing diagnostic card %s in KB", card_id)
            return False
