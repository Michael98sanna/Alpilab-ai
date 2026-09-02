"""Continuous learning engine for ALPILAB Brain."""



from __future__ import annotations



import logging

import re

import uuid

from datetime import UTC, datetime, timedelta



from sqlalchemy import func

from sqlalchemy.orm import Session



from app.ai.smart_knowledge_base import SmartKnowledgeBase

from app.models.orm_models import (

    DiagnosisConfirmation,

    KnowledgeEmbedding,

    LearningMetric,

    ProviderMetric,

    RouteEvent,

)



logger = logging.getLogger(__name__)



_ROUTE_EVENT_RETENTION_DAYS = 180



_DIAGNOSIS_KEYWORDS: dict[str, tuple[str, ...]] = {

    "battery": ("batteria", "battery", "tensione", "voltage", "carica lenta"),

    "display": ("display", "schermo", "lcd", "oled", "touch", "vetro"),

    "thermal": ("surriscalda", "thermal", "caldo", "overheat", "temperatura"),

    "connector": ("connettore", "connector", "dock", "flex", "fpc"),

    "charging": ("carica", "charging", "usb", "lightning", "type-c"),

    "water": ("acqua", "water", "ossidazione", "liquid", "umidità"),

    "software": ("software", "ios", "boot loop", "restore", "dfu", "update"),

    "board": ("board", "scheda", "pmic", "ic", "short", "corto"),

}





class LearningEngine:

    """Records feedback and updates knowledge + metrics."""



    def __init__(self, db: Session, *, kb: SmartKnowledgeBase | None = None) -> None:

        self.db = db

        self.kb = kb or SmartKnowledgeBase(db)



    @staticmethod

    def extract_diagnosis_category(text: str) -> str:

        normalized = text.lower()

        for category, keywords in _DIAGNOSIS_KEYWORDS.items():

            if any(keyword in normalized for keyword in keywords):

                return category

        return "unknown"



    def record_feedback(

        self,

        *,

        card_id: str,

        feedback: str,

        provider: str | None,

        pre_confidence: float,

        knowledge_entry_id: str | None = None,

        correction_text: str | None = None,

        ai_diagnosis: str | None = None,

    ) -> DiagnosisConfirmation:

        confirmation = DiagnosisConfirmation(

            id=str(uuid.uuid4()),

            card_id=card_id,

            ai_diagnosis=ai_diagnosis,

            feedback=feedback,

            correction_text=correction_text,

            provider=provider,

            pre_feedback_confidence=pre_confidence,

            knowledge_entry_id=knowledge_entry_id,

        )

        self.db.add(confirmation)

        self.db.commit()

        self.db.refresh(confirmation)

        return confirmation



    def record_outcome(

        self,

        confirmation_id: str,

        *,

        outcome: str,

        notes: str | None = None,

        symptom_text: str = "",

        device_type: str = "unknown",

        ai_diagnosis: str = "",

        ai_solution: str = "",

    ) -> DiagnosisConfirmation | None:

        confirmation = self.db.get(DiagnosisConfirmation, confirmation_id)

        if not confirmation:

            return None



        confirmation.repair_outcome = outcome

        confirmation.outcome_notes = notes

        confirmation.outcome_at = datetime.now(UTC)

        diagnosis_type = self.extract_diagnosis_category(

            symptom_text or ai_diagnosis or confirmation.correction_text or ""

        )



        feedback = confirmation.feedback

        entry_id = confirmation.knowledge_entry_id



        if feedback == "confirmed" and outcome == "success":
            if confirmation.provider == "ollama":
                logger.info(
                    "Skipping authoritative KB indexing for local Ollama confirmation %s",
                    confirmation.id,
                )
            elif entry_id:
                self.kb.boost_confidence(entry_id, amount=0.12)
            else:
                self.kb.index_case(
                    text=symptom_text or ai_diagnosis,
                    diagnosis=ai_diagnosis,
                    solution=ai_solution,
                    diagnosis_type=diagnosis_type,
                    device_type=device_type,
                    confidence=0.9,
                )
            self._update_metrics(diagnosis_type, confirmation.provider, correct=True)

        elif feedback == "corrected" and confirmation.correction_text:
            if confirmation.provider != "ollama":
                self.kb.index_case(
                    text=symptom_text or confirmation.correction_text,
                    diagnosis=confirmation.correction_text,
                    solution=ai_solution or notes or "",
                    diagnosis_type=diagnosis_type,
                    device_type=device_type,
                    confidence=0.9,
                    source_card_id=confirmation.card_id,
                )
            else:
                logger.info(
                    "Skipping KB indexing for corrected Ollama case %s",
                    confirmation.id,
                )

            if entry_id:

                self.kb.decay_confidence(entry_id, delta=0.2)

            self._update_metrics(diagnosis_type, confirmation.provider, correct=True, weight=0.5)



        elif feedback == "rejected" or outcome == "failed":

            if entry_id:

                self.kb.decay_confidence(entry_id, delta=0.25)

            self._update_metrics(diagnosis_type, confirmation.provider, correct=False)



        elif outcome == "partial":

            self._update_metrics(diagnosis_type, confirmation.provider, correct=False, weight=0.5)



        self.db.commit()

        self.db.refresh(confirmation)

        return confirmation



    def record_route_event(

        self,

        *,

        diagnosis_type: str,

        kb_mode: str,

        strong_match: bool,

        used_online: bool,

        provider: str | None,

        latency_ms: int,

        cost_estimate: float = 0.0,

    ) -> RouteEvent:

        event = RouteEvent(

            id=str(uuid.uuid4()),

            timestamp=datetime.now(UTC),

            diagnosis_type=diagnosis_type or "unknown",

            kb_mode=kb_mode,

            strong_match=strong_match,

            used_online=used_online,

            provider=provider,

            latency_ms=latency_ms,

            cost_estimate=cost_estimate,

        )

        self.db.add(event)

        self.db.commit()

        return event



    def purge_old_route_events(self, *, days: int = _ROUTE_EVENT_RETENTION_DAYS) -> int:

        cutoff = datetime.now(UTC) - timedelta(days=days)

        deleted = (

            self.db.query(RouteEvent)

            .filter(RouteEvent.timestamp < cutoff)

            .delete(synchronize_session=False)

        )

        if deleted:

            self.db.commit()

        return deleted



    def get_kb_maturity(self) -> dict:

        indexed_cases = (

            self.db.query(KnowledgeEmbedding)

            .filter(

                KnowledgeEmbedding.excluded.is_(False),

                KnowledgeEmbedding.disputed.is_(False),

            )

            .count()

        )



        type_rows = (

            self.db.query(

                KnowledgeEmbedding.diagnosis_type,

                func.count(KnowledgeEmbedding.id),

            )

            .filter(

                KnowledgeEmbedding.excluded.is_(False),

                KnowledgeEmbedding.disputed.is_(False),

            )

            .group_by(KnowledgeEmbedding.diagnosis_type)

            .all()

        )

        cases_by_type = {row[0]: row[1] for row in type_rows}



        cutoff = datetime.now(UTC) - timedelta(days=30)

        events = (

            self.db.query(RouteEvent)

            .filter(RouteEvent.timestamp >= cutoff)

            .all()

        )

        total_requests = len(events)

        strong_hits = sum(1 for event in events if event.strong_match)

        local_hit_rate_30d = strong_hits / total_requests if total_requests else 0.0

        estimated_api_calls_saved = strong_hits



        if indexed_cases < 10:

            maturity_stage = "cold"

        elif indexed_cases >= 50 and local_hit_rate_30d > 0.30:

            maturity_stage = "mature"

        else:

            maturity_stage = "warming"



        return {

            "indexed_cases": indexed_cases,

            "cases_by_type": cases_by_type,

            "local_hit_rate_30d": round(local_hit_rate_30d, 4),

            "estimated_api_calls_saved": estimated_api_calls_saved,

            "maturity_stage": maturity_stage,

        }



    def get_accuracy(self, diagnosis_type: str | None = None) -> dict:

        query = self.db.query(LearningMetric)

        if diagnosis_type:

            row = query.filter(LearningMetric.diagnosis_type == diagnosis_type).first()

            if not row:

                return {"diagnosis_type": diagnosis_type, "accuracy": 0.0, "total": 0}

            return {

                "diagnosis_type": row.diagnosis_type,

                "accuracy": row.accuracy,

                "total": row.total_cases,

                "correct": row.correct_cases,

                "avg_confidence": row.avg_confidence,

            }



        rows = query.all()

        if not rows:

            return {"global_accuracy": 0.0, "by_type": []}

        total = sum(row.total_cases for row in rows)

        correct = sum(row.correct_cases for row in rows)

        return {

            "global_accuracy": correct / total if total else 0.0,

            "by_type": [

                {

                    "diagnosis_type": row.diagnosis_type,

                    "accuracy": row.accuracy,

                    "total": row.total_cases,

                    "correct": row.correct_cases,

                }

                for row in rows

            ],

        }



    def get_provider_metrics(self) -> list[dict]:

        rows = self.db.query(ProviderMetric).all()

        return [

            {

                "provider": row.provider,

                "diagnosis_type": row.diagnosis_type,

                "accuracy": row.accuracy,

                "total": row.total_cases,

                "correct": row.correct_cases,

                "avg_latency_ms": row.avg_latency_ms,

            }

            for row in rows

        ]



    def get_diagnosis_accuracy(self, diagnosis_type: str | None = None) -> dict:

        return self.get_accuracy(diagnosis_type)



    def get_all_accuracies(self) -> dict:

        payload = self.get_accuracy()

        payload["kb_maturity"] = self.get_kb_maturity()

        return payload



    def _update_metrics(

        self,

        diagnosis_type: str,

        provider: str | None,

        *,

        correct: bool,

        weight: float = 1.0,

        latency_ms: float = 0.0,

    ) -> None:

        metric = (

            self.db.query(LearningMetric)

            .filter(LearningMetric.diagnosis_type == diagnosis_type)

            .first()

        )

        if metric is None:

            metric = LearningMetric(

                diagnosis_type=diagnosis_type,

                total_cases=0,

                correct_cases=0,

                accuracy=0.0,

                avg_confidence=0.0,

            )

            self.db.add(metric)

        metric.total_cases = (metric.total_cases or 0) + 1

        if correct:

            metric.correct_cases += weight

        metric.accuracy = metric.correct_cases / metric.total_cases if metric.total_cases else 0.0

        metric.avg_confidence = metric.accuracy

        month_key = datetime.now(UTC).strftime("%Y-%m")

        evolution = dict(metric.confidence_evolution or {})

        evolution[month_key] = round(metric.accuracy, 4)

        metric.confidence_evolution = evolution

        metric.last_updated = datetime.now(UTC)



        if provider:

            pm = (

                self.db.query(ProviderMetric)

                .filter(

                    ProviderMetric.provider == provider,

                    ProviderMetric.diagnosis_type == diagnosis_type,

                )

                .first()

            )

            if pm is None:

                pm = ProviderMetric(

                    provider=provider,

                    diagnosis_type=diagnosis_type,

                    total_cases=0,

                    correct_cases=0,

                    accuracy=0.0,

                    avg_latency_ms=0.0,

                )

                self.db.add(pm)

            pm.total_cases = (pm.total_cases or 0) + 1

            if correct:

                pm.correct_cases += 1

            pm.accuracy = pm.correct_cases / pm.total_cases

            if latency_ms:

                pm.avg_latency_ms = (

                    pm.avg_latency_ms * (pm.total_cases - 1) + latency_ms

                ) / pm.total_cases



        self.db.commit()

