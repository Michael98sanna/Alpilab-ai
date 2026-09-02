"""REST API for ALPILAB Brain AI."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.ai.conversation_ai import ConversationAI
from app.ai.learning_engine import LearningEngine
from app.ai.providers.diagnostics import build_provider_status
from app.ai.providers.registry import load_providers
from app.ai.smart_knowledge_base import SmartKnowledgeBase
from app.models.database import get_db
from app.schemas.ai import (
    BrainChatRequest,
    BrainChatResponse,
    BrainFeedbackRequest,
    BrainFeedbackResponse,
    BrainOutcomeRequest,
    BrainOutcomeResponse,
    KBSearchResult,
)
from app.services.diagnostic_card_service import DiagnosticCardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Brain"])

_provider_status_cache: dict[str, Any] = {"ts": 0.0, "payload": {}}
_STATUS_TTL_SEC = 60.0


def _empty_brain_metrics() -> dict[str, Any]:
    return {
        "global_accuracy": 0.0,
        "by_type": [],
        "kb_maturity": {
            "indexed_cases": 0,
            "cases_by_type": {},
            "local_hit_rate_30d": 0.0,
            "estimated_api_calls_saved": 0,
            "maturity_stage": "cold",
        },
    }


@router.post("/chat", response_model=BrainChatResponse)
def brain_chat(body: BrainChatRequest, db: Session = Depends(get_db)) -> BrainChatResponse:
    try:
        payload = ConversationAI(db).process_message(body.card_id, body.message)
        return BrainChatResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Brain chat failed")
        raise HTTPException(status_code=500, detail="Brain chat failed") from exc


@router.post("/{card_id}/feedback", response_model=BrainFeedbackResponse)
def card_feedback(
    card_id: str,
    body: BrainFeedbackRequest,
    db: Session = Depends(get_db),
) -> BrainFeedbackResponse:
    service = DiagnosticCardService(db)
    card = service.get_card(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    if body.feedback == "corrected" and not (body.correction_text or "").strip():
        raise HTTPException(status_code=400, detail="correction_text required")

    confirmation = LearningEngine(db).record_feedback(
        card_id=card_id,
        feedback=body.feedback,
        provider=body.provider,
        pre_confidence=body.pre_confidence,
        knowledge_entry_id=body.knowledge_entry_id,
        correction_text=body.correction_text,
        ai_diagnosis=body.ai_diagnosis or card.hypothesis,
    )
    return BrainFeedbackResponse(confirmation_id=confirmation.id)


@router.post("/cards/{card_id}/feedback", response_model=BrainFeedbackResponse)
def card_feedback_legacy(
    card_id: str,
    body: BrainFeedbackRequest,
    db: Session = Depends(get_db),
) -> BrainFeedbackResponse:
    return card_feedback(card_id, body, db)


@router.post("/confirmation/{confirmation_id}/outcome", response_model=BrainOutcomeResponse)
def confirmation_outcome(
    confirmation_id: str,
    body: BrainOutcomeRequest,
    db: Session = Depends(get_db),
) -> BrainOutcomeResponse:
    from app.models.orm_models import DiagnosisConfirmation

    confirmation = db.get(DiagnosisConfirmation, confirmation_id)
    if not confirmation:
        raise HTTPException(status_code=404, detail="Confirmation not found")

    card = DiagnosticCardService(db).get_card(confirmation.card_id)
    engine = LearningEngine(db)
    updated = engine.record_outcome(
        confirmation_id,
        outcome=body.outcome,
        notes=body.notes,
        symptom_text=card.current_symptom if card else "",
        device_type=card.device_id if card else "unknown",
        ai_diagnosis=card.hypothesis if card else "",
        ai_solution=card.solution_applied if card else "",
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Confirmation not found")
    return BrainOutcomeResponse(confirmation_id=updated.id)


@router.post("/confirmations/{confirmation_id}/outcome", response_model=BrainOutcomeResponse)
def confirmation_outcome_legacy(
    confirmation_id: str,
    body: BrainOutcomeRequest,
    db: Session = Depends(get_db),
) -> BrainOutcomeResponse:
    return confirmation_outcome(confirmation_id, body, db)


@router.get("/metrics")
def brain_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return LearningEngine(db).get_all_accuracies()
    except Exception:
        logger.exception("Brain metrics unavailable")
        return _empty_brain_metrics()


@router.get("/metrics/providers")
def provider_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return {"providers": LearningEngine(db).get_provider_metrics()}
    except Exception:
        logger.exception("Provider metrics unavailable")
        return {"providers": []}


@router.get("/metrics/{diagnosis_type}")
def brain_metrics_by_type(diagnosis_type: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return LearningEngine(db).get_diagnosis_accuracy(diagnosis_type)
    except Exception:
        logger.exception("Brain metrics by type unavailable")
        return {"diagnosis_type": diagnosis_type, "accuracy": 0.0, "total": 0}


@router.get("/providers/status")
def providers_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    now = time.time()
    if now - float(_provider_status_cache["ts"]) < _STATUS_TTL_SEC:
        return _provider_status_cache["payload"]

    status = build_provider_status(live=True)
    kb = SmartKnowledgeBase(db)
    indexed_cases = kb.indexed_case_count()
    kb_mode = kb.embedder_kind if indexed_cases > 0 else "disabled"
    configured = {provider.name: provider for provider in load_providers()}
    payload = {
        "config": status["config"],
        "providers": [
            {
                "name": row["name"],
                "model": configured[row["name"]].model if row["name"] in configured else row.get("model"),
                "configured": row["key_present"],
                "healthy": row["available"],
                "priority": configured[row["name"]].priority if row["name"] in configured else 99,
                "key_present": row["key_present"],
                "key_shape_valid": row["key_shape_valid"],
                "available": row["available"],
                "error_kind": row["error_kind"],
                "latency_ms": row.get("latency_ms"),
            }
            for row in status["providers"]
        ],
        "online_available": status["online_available"],
        "offline_mode": status["offline_mode"],
        "brain_mode": status["brain_mode"],
        "kb": {
            "mode": kb_mode,
            "model_name": kb.model_name,
            "indexed_cases": indexed_cases,
        },
    }
    _provider_status_cache["ts"] = now
    _provider_status_cache["payload"] = payload
    return payload


@router.get("/kb/search", response_model=list[KBSearchResult])
def kb_search(
    q: str = Query(..., min_length=1),
    diagnosis_type: str | None = None,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[KBSearchResult]:
    cases = SmartKnowledgeBase(db).search_similar(
        q,
        top_k=top_k,
        diagnosis_type=diagnosis_type,
    )
    return [
        KBSearchResult(
            id=case.id,
            text=case.text,
            diagnosis=case.diagnosis,
            solution=case.solution,
            diagnosis_type=case.diagnosis_type,
            device_type=case.device_type,
            confidence_score=case.confidence_score,
            similarity=round(case.similarity, 4),
        )
        for case in cases
    ]
