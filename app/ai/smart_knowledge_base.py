"""Semantic knowledge base for the Brain learning loop."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import numpy as np
from sqlalchemy.orm import Session

from app.ai.schemas import KnowledgeCase
from app.models.orm_models import KnowledgeEmbedding

logger = logging.getLogger(__name__)

STRONG_MATCH_THRESHOLD = 0.80
LOCAL_KB_CONFIDENCE = 0.75
WEAK_MATCH_SIMILARITY = 0.50
EXCLUDE_CONFIDENCE = 0.3
DISPUTED_THRESHOLD = 0.4
DECAY_AFTER_DAYS = 90
_HASH_MODE_WARNED = False


class SmartKnowledgeBase:
    """Embedding-backed knowledge with full-text fallback."""

    def __init__(self, db: Session, *, embedder: Any | None = None) -> None:
        self.db = db
        self._embedder = embedder

    def _resolve_embedder(self) -> Any:
        global _HASH_MODE_WARNED
        if self._embedder is None:
            try:
                from app.knowledge.embeddings import default_embedder

                self._embedder = default_embedder()
            except Exception:
                from app.knowledge.embeddings import HashEmbedder

                self._embedder = HashEmbedder()
        if not _HASH_MODE_WARNED:
            from app.knowledge.embeddings import LazySentenceTransformerEmbedder

            if not isinstance(self._embedder, LazySentenceTransformerEmbedder):
                logger.warning(
                    "Ricerca semantica KB non attiva: sentence-transformers assente. "
                    "La memoria locale non verrà usata per match forti — installa "
                    "sentence-transformers per abilitarla."
                )
                _HASH_MODE_WARNED = True
        return self._embedder

    @property
    def embedder(self) -> Any:
        return self._resolve_embedder()

    @property
    def embedder_kind(self) -> Literal["semantic", "hash"]:
        from app.knowledge.embeddings import LazySentenceTransformerEmbedder

        if isinstance(self._resolve_embedder(), LazySentenceTransformerEmbedder):
            return "semantic"
        return "hash"

    @property
    def is_semantic(self) -> bool:
        return self.embedder_kind == "semantic"

    @property
    def strong_match_threshold(self) -> float | None:
        return STRONG_MATCH_THRESHOLD if self.is_semantic else None

    @property
    def model_name(self) -> str | None:
        from app.knowledge.embeddings import LazySentenceTransformerEmbedder

        embedder = self._resolve_embedder()
        if isinstance(embedder, LazySentenceTransformerEmbedder):
            return embedder.model_name
        return None

    def indexed_case_count(self) -> int:
        return (
            self.db.query(KnowledgeEmbedding)
            .filter(
                KnowledgeEmbedding.excluded.is_(False),
                KnowledgeEmbedding.disputed.is_(False),
            )
            .count()
        )

    def index_diagnosis(
        self,
        *,
        text: str,
        diagnosis: str,
        solution: str,
        diagnosis_type: str,
        device_type: str,
        confidence: float = 0.85,
        source_card_id: str | None = None,
        entry_id: str | None = None,
    ) -> KnowledgeEmbedding:
        return self.index_case(
            text=text,
            diagnosis=diagnosis,
            solution=solution,
            diagnosis_type=diagnosis_type,
            device_type=device_type,
            confidence=confidence,
            source_card_id=source_card_id,
            entry_id=entry_id,
        )

    def index_case(
        self,
        *,
        text: str,
        diagnosis: str,
        solution: str,
        diagnosis_type: str,
        device_type: str,
        confidence: float = 0.85,
        source_card_id: str | None = None,
        entry_id: str | None = None,
    ) -> KnowledgeEmbedding:
        embedding = self.embedder.encode(text.strip()).tolist()
        now = datetime.now(UTC)
        entry = KnowledgeEmbedding(
            id=entry_id or str(uuid.uuid4()),
            source_card_id=source_card_id,
            text=text.strip(),
            diagnosis=diagnosis.strip(),
            solution=solution.strip(),
            embedding_json=embedding,
            diagnosis_type=diagnosis_type,
            device_type=device_type,
            confidence_score=min(max(confidence, 0.0), 1.0),
            confirmation_count=1,
            created_at=now,
            last_used=now,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def search_similar(
        self,
        query: str,
        *,
        top_k: int = 5,
        diagnosis_type: str | None = None,
        device_type: str | None = None,
        min_confidence: float = EXCLUDE_CONFIDENCE,
    ) -> list[KnowledgeCase]:
        return self.search(
            query,
            diagnosis_type=diagnosis_type,
            device_type=device_type,
            min_confidence=min_confidence,
            limit=top_k,
        )

    def search(
        self,
        query: str,
        *,
        diagnosis_type: str | None = None,
        device_type: str | None = None,
        min_confidence: float = EXCLUDE_CONFIDENCE,
        limit: int = 5,
    ) -> list[KnowledgeCase]:
        entries = (
            self.db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .filter(KnowledgeEmbedding.disputed.is_(False))
            .filter(KnowledgeEmbedding.confidence_score >= min_confidence)
            .all()
        )
        if not entries:
            return self._fulltext_search(query, diagnosis_type, device_type, limit)

        query_vec = np.asarray(self.embedder.encode(query.strip()), dtype=np.float64)
        results: list[KnowledgeCase] = []
        for entry in entries:
            if diagnosis_type and entry.diagnosis_type != diagnosis_type:
                continue
            if device_type and entry.device_type != device_type and device_type != "unknown":
                continue
            vec = np.asarray(entry.embedding_json, dtype=np.float64)
            similarity = _cosine(query_vec, vec)
            entry.usage_count += 1
            entry.last_used = datetime.now(UTC)
            results.append(
                KnowledgeCase(
                    id=entry.id,
                    text=entry.text,
                    diagnosis_type=entry.diagnosis_type,
                    device_type=entry.device_type,
                    diagnosis=entry.diagnosis,
                    solution=entry.solution,
                    confidence_score=entry.confidence_score,
                    confirmation_count=entry.confirmation_count,
                    similarity=similarity,
                )
            )
        self.db.commit()
        results.sort(key=lambda item: item.similarity, reverse=True)
        return results[:limit]

    def boost_confidence(self, entry_id: str, amount: float = 0.1) -> None:
        entry = self.db.get(KnowledgeEmbedding, entry_id)
        if not entry:
            return
        entry.confidence_score = min(1.0, entry.confidence_score + amount)
        if entry.confidence_score >= DISPUTED_THRESHOLD:
            entry.disputed = False
        entry.confirmation_count += 1
        self.db.commit()

    def penalize_confidence(self, entry_id: str, amount: float = 0.15) -> float | None:
        entry = self.db.get(KnowledgeEmbedding, entry_id)
        if not entry:
            return None
        before = entry.confidence_score
        entry.confidence_score = max(0.1, entry.confidence_score - amount)
        if entry.confidence_score < DISPUTED_THRESHOLD:
            entry.disputed = True
        self.db.commit()
        return before

    def decay_confidence(self, entry_id: str, delta: float = 0.15) -> None:
        entry = self.db.get(KnowledgeEmbedding, entry_id)
        if not entry:
            return
        entry.confidence_score = max(0.0, entry.confidence_score - delta)
        if entry.confidence_score < EXCLUDE_CONFIDENCE:
            entry.excluded = True
        if entry.confidence_score < DISPUTED_THRESHOLD:
            entry.disputed = True
        self.db.commit()

    def decay_unused(self, *, days: int = DECAY_AFTER_DAYS, delta: float = 0.05) -> int:
        """Lower confidence for entries not used recently."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        entries = (
            self.db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .all()
        )
        affected = 0
        for entry in entries:
            last = entry.last_used or entry.created_at
            if last and last.replace(tzinfo=UTC) < cutoff:
                entry.confidence_score = max(0.0, entry.confidence_score - delta)
                if entry.confidence_score < EXCLUDE_CONFIDENCE:
                    entry.excluded = True
                if entry.confidence_score < DISPUTED_THRESHOLD:
                    entry.disputed = True
                affected += 1
        if affected:
            self.db.commit()
        return affected

    def best_local_match(self, cases: list[KnowledgeCase]) -> KnowledgeCase | None:
        threshold = self.strong_match_threshold
        if threshold is None:
            return None
        for case in cases:
            if (
                case.similarity >= threshold
                and case.confidence_score >= LOCAL_KB_CONFIDENCE
            ):
                return case
        return None

    def _fulltext_search(
        self,
        query: str,
        diagnosis_type: str | None,
        device_type: str | None,
        limit: int,
    ) -> list[KnowledgeCase]:
        tokens = query.lower().split()
        q = (
            self.db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .filter(KnowledgeEmbedding.disputed.is_(False))
        )
        if diagnosis_type:
            q = q.filter(KnowledgeEmbedding.diagnosis_type == diagnosis_type)
        if device_type and device_type != "unknown":
            q = q.filter(KnowledgeEmbedding.device_type == device_type)
        entries = q.all()
        scored: list[KnowledgeCase] = []
        for entry in entries:
            hay = f"{entry.text} {entry.diagnosis} {entry.solution}".lower()
            hits = sum(1 for token in tokens if token in hay)
            if hits == 0:
                continue
            scored.append(
                KnowledgeCase(
                    id=entry.id,
                    text=entry.text,
                    diagnosis_type=entry.diagnosis_type,
                    device_type=entry.device_type,
                    diagnosis=entry.diagnosis,
                    solution=entry.solution,
                    confidence_score=entry.confidence_score,
                    confirmation_count=entry.confirmation_count,
                    similarity=min(1.0, hits / max(len(tokens), 1)),
                )
            )
        scored.sort(key=lambda item: item.similarity, reverse=True)
        return scored[:limit]


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
