"""RAG-enabled knowledge base with semantic search."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.knowledge.embeddings import Embedder, default_embedder
from app.knowledge.models import KnowledgeEntryModel
from app.knowledge.records import RepairKnowledgeRecord
from app.schemas.session import RepairSessionContext

logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """Raised when knowledge-base operations fail."""


class KnowledgeBase:
    """RAG-enabled knowledge base with embeddings."""

    def __init__(
        self,
        db: Session,
        *,
        embedder: Embedder | None = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or default_embedder()

    def index_repair(self, session: RepairSessionContext | RepairKnowledgeRecord) -> KnowledgeEntryModel:
        """Index a completed repair case."""
        record = (
            session
            if isinstance(session, RepairKnowledgeRecord)
            else RepairKnowledgeRecord.from_session_context(session)
        )
        symptom_text = " ".join(record.symptoms) if record.symptoms else "unknown"
        embedding = self.embedder.encode(symptom_text).tolist()

        try:
            existing = (
                self.db.query(KnowledgeEntryModel)
                .filter(KnowledgeEntryModel.id == record.session_id)
                .first()
            )
            success_rate = 1.0 if record.status == "completed" else 0.0

            if existing:
                existing.device = record.device_model
                existing.brand = record.device_brand
                existing.symptom = symptom_text
                existing.diagnosis = record.diagnosis
                existing.solution = record.solution
                existing.technical_notes = record.technical_notes
                existing.embedding_vector = embedding
                existing.repair_duration_min = record.repair_duration_min
                existing.success_rate = success_rate
                entry = existing
            else:
                entry = KnowledgeEntryModel(
                    id=record.session_id,
                    device=record.device_model,
                    brand=record.device_brand,
                    symptom=symptom_text,
                    diagnosis=record.diagnosis,
                    solution=record.solution,
                    technical_notes=record.technical_notes,
                    embedding_vector=embedding,
                    repair_duration_min=record.repair_duration_min,
                    success_rate=success_rate,
                )
                self.db.add(entry)

            self.db.commit()
            self.db.refresh(entry)
            return entry
        except SQLAlchemyError as exc:
            self.db.rollback()
            logger.exception("Failed to index repair %s", record.session_id)
            raise KnowledgeBaseError(
                f"Failed to index repair {record.session_id}"
            ) from exc

    def search_similar(
        self,
        symptom: str,
        device: str | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Search similar repair cases by embedding cosine similarity."""
        if not symptom.strip():
            raise ValueError("symptom is required")
        if limit < 1:
            raise ValueError("limit must be >= 1")

        symptom_embedding = self.embedder.encode(symptom.strip())
        all_entries = self.db.query(KnowledgeEntryModel).all()
        if not all_entries:
            return []

        results: list[dict[str, Any]] = []
        for entry in all_entries:
            vector = np.array(entry.embedding_vector, dtype=np.float64)
            similarity = self._cosine_similarity(symptom_embedding, vector)

            if device and entry.device != device:
                similarity *= 0.7

            results.append(
                {
                    "device": entry.device,
                    "symptom": entry.symptom,
                    "diagnosis": entry.diagnosis,
                    "solution": entry.solution,
                    "repair_duration_min": entry.repair_duration_min,
                    "success_rate": entry.success_rate,
                    "similarity": float(similarity),
                }
            )

        results.sort(key=lambda item: item["similarity"], reverse=True)
        return results[:limit]

    def get_rag_context(self, symptom: str, device: str | None = None) -> str:
        """Build RAG context text for AI prompt augmentation."""
        similar = self.search_similar(symptom, device, limit=3)
        if not similar:
            return ""

        lines = ["Casi simili trovati nel laboratorio:"]
        for index, case in enumerate(similar, 1):
            lines.append(f"\n{index}. {case['device']} - {case['symptom']}")
            lines.append(f"   Diagnosi: {case['diagnosis']}")
            lines.append(f"   Soluzione: {case['solution']}")
            lines.append(f"   Confidenza: {case['similarity']:.0%}")
        return "\n".join(lines)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
