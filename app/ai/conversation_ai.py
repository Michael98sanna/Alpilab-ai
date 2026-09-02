"""Conversation orchestrator for diagnostic cards."""

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.ai.router import BrainRouter
from app.ai.schemas import IntelligentRouteResult, ResponseSource, TaskType
from app.ai.task_classifier import classify_task
from app.services.diagnostic_card_service import DiagnosticCardService

logger = logging.getLogger(__name__)

_HYPOTHESIS_PATTERN = re.compile(
    r"(?:diagnosi|ipotesi|probabile causa)[:\s]+(.+?)(?:\.|$)",
    re.IGNORECASE,
)


class ConversationAI:
    """Handles card-scoped AI chat with Brain routing."""

    def __init__(self, db: Session, *, router: BrainRouter | None = None) -> None:
        self.db = db
        self.cards = DiagnosticCardService(db)
        self.router = router or BrainRouter(db)

    def chat(self, card_id: str, message: str) -> dict[str, Any]:
        return self.process_message(card_id, message)

    def process_message(self, card_id: str, user_input: str) -> dict[str, Any]:
        card = self.cards.get_card(card_id)
        if not card:
            raise ValueError(f"Card {card_id} not found")

        history = self.cards.get_conversation_history(card_id)
        context_lines = [
            f"Device: {card.device_name} ({card.device_id})",
            f"Sintomo attuale: {card.current_symptom or 'non specificato'}",
            f"Ipotesi corrente: {card.hypothesis or 'nessuna'}",
        ]
        for item in history[-6:]:
            context_lines.append(f"{item['role']}: {item['content'][:200]}")

        message = user_input.strip()
        enriched_prompt = "\n".join(context_lines) + f"\nuser: {message}"
        symptom = card.current_symptom or message
        diagnosis_type = self.router.learning.extract_diagnosis_category(symptom)

        try:
            result = self.router.intelligent_route(
                enriched_prompt,
                device_type=card.device_id,
                symptom=symptom,
                diagnosis_type=diagnosis_type,
            )
        except Exception:
            logger.exception("Brain routing failed for card %s", card_id)
            from app.ai.providers.diagnostics import build_chat_fallback_message

            result = IntelligentRouteResult(
                content=build_chat_fallback_message(),
                source=ResponseSource.ONLINE,
                provider="none",
                model="none",
                confidence=0.0,
                task_type=classify_task(message),
                similar_cases=[],
                latency_ms=0,
                used_online=False,
                kb_hits=0,
            )

        self.cards.add_message(card_id, "user", message)
        self.cards.add_message(
            card_id,
            "assistant",
            result.content,
            tool_calls={
                "brain": {
                    "provider": result.provider,
                    "model": result.model,
                    "source": result.source.value,
                    "confidence": result.confidence,
                    "task_type": result.task_type.value,
                    "diagnosis_type": diagnosis_type,
                    "similar_cases": len(result.similar_cases),
                    "kb_hits": result.kb_hits,
                    "used_online": result.used_online,
                    "latency_ms": result.latency_ms,
                    "knowledge_entry_id": result.metadata.get("knowledge_entry_id"),
                    "low_accuracy_warning": result.low_accuracy_warning,
                    "kb_mode": result.kb_mode,
                    "strong_match": result.strong_match,
                    "local_model": result.provider == "ollama",
                    "validation": result.validation.model_dump(),
                }
            },
        )

        hypothesis = self._extract_hypothesis(result.content) or card.hypothesis
        updates: dict[str, Any] = {
            "confidence": result.confidence,
        }
        if not card.current_symptom and message:
            updates["current_symptom"] = message[:500]
        if hypothesis:
            updates["hypothesis"] = hypothesis[:500]
            updates["diagnostic_stage"] = "hypothesis"
        self.cards.update_card_state(card_id, updates)

        return {
            "content": result.content,
            "provider": result.provider,
            "model": result.model,
            "source": result.source.value,
            "confidence": result.confidence,
            "task_type": result.task_type.value,
            "diagnosis_type": diagnosis_type,
            "similar_cases_count": len(result.similar_cases),
            "kb_hits": result.kb_hits,
            "used_online": result.used_online,
            "similar_cases": [
                {
                    "id": case.id,
                    "diagnosis": case.diagnosis,
                    "similarity": round(case.similarity, 3),
                    "confidence": case.confidence_score,
                }
                for case in result.similar_cases[:3]
            ],
            "latency_ms": result.latency_ms,
            "low_accuracy_warning": result.low_accuracy_warning,
            "knowledge_entry_id": result.metadata.get("knowledge_entry_id"),
            "kb_mode": result.kb_mode,
            "strong_match": result.strong_match,
            "local_model": result.provider == "ollama",
            "validation": result.validation.model_dump(),
        }

    @staticmethod
    def _extract_hypothesis(text: str) -> str | None:
        match = _HYPOTHESIS_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        if "probabile" in text.lower() and len(text) < 400:
            return text.strip()[:200]
        return None
