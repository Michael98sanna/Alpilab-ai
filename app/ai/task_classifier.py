"""Intent classification for Brain routing."""

from __future__ import annotations

import logging
import re

from app.ai.schemas import TaskType

logger = logging.getLogger(__name__)

_KEYWORD_RULES: list[tuple[TaskType, tuple[str, ...]]] = [
    (
        TaskType.CODE_ANALYSIS,
        (
            "panic log",
            "panic",
            "stack trace",
            "error log",
            "log iphone",
            "analizza log",
            "analyze log",
            "kernel panic",
            "crash log",
        ),
    ),
    (
        TaskType.KNOWLEDGE_SEARCH,
        (
            "listino",
            "prezzo",
            "ricambio",
            "schema",
            "schematic",
            "componente",
            "part number",
            "dove trovo",
            "cerca",
            "search",
            "already seen",
            "già successo",
            "altri iphone",
            "altri casi",
        ),
    ),
    (
        TaskType.DIAGNOSIS,
        (
            "non si accende",
            "won't turn on",
            "display",
            "schermo",
            "batteria",
            "battery",
            "carica",
            "charging",
            "usb",
            "thermal",
            "surriscalda",
            "overheat",
            "acqua",
            "water damage",
            "connettore",
            "connector",
            "diagnosi",
            "diagnosis",
            "sintomo",
            "symptom",
            "riparazione",
            "repair",
        ),
    ),
    (
        TaskType.REASONING,
        (
            "perché",
            "why",
            "causa",
            "cause",
            "ipotesi",
            "hypothesis",
            "probabile",
            "likely",
            "ragionamento",
        ),
    ),
    (
        TaskType.EXPLANATION,
        (
            "spiega",
            "explain",
            "come funziona",
            "how does",
            "cos'è",
            "what is",
        ),
    ),
    (
        TaskType.QUICK_ANSWER,
        (
            "quanto",
            "how much",
            "quando",
            "when",
            "sì o no",
            "yes or no",
        ),
    ),
]


def classify_task(text: str) -> TaskType:
    """Classify user message intent using keywords with optional semantic fallback."""
    normalized = text.lower().strip()
    if not normalized:
        return TaskType.QUICK_ANSWER

    for task_type, keywords in _KEYWORD_RULES:
        if any(keyword in normalized for keyword in keywords):
            return task_type

    semantic = _semantic_classify(normalized)
    if semantic is not None:
        return semantic

    if re.search(r"\?", normalized):
        return TaskType.EXPLANATION
    return TaskType.DIAGNOSIS


def _semantic_classify(text: str) -> TaskType | None:
    """Optional sentence-transformers backend from intent_parser_v2."""
    try:
        from app.commands.intent_parser_v2 import default_embedder

        embedder = default_embedder()
        prototypes = {
            TaskType.DIAGNOSIS: "smartphone repair diagnosis symptom hardware failure",
            TaskType.KNOWLEDGE_SEARCH: "search parts price schematic information",
            TaskType.CODE_ANALYSIS: "analyze panic log error crash stack trace",
            TaskType.REASONING: "explain cause hypothesis reasoning",
            TaskType.EXPLANATION: "explain how it works tutorial",
            TaskType.QUICK_ANSWER: "short factual answer",
        }
        import numpy as np

        query = np.asarray(embedder.encode(text), dtype=np.float64)
        best_type: TaskType | None = None
        best_score = 0.0
        for task_type, proto in prototypes.items():
            vec = np.asarray(embedder.encode(proto), dtype=np.float64)
            denom = float(np.linalg.norm(query) * np.linalg.norm(vec))
            score = float(np.dot(query, vec) / denom) if denom else 0.0
            if score > best_score:
                best_score = score
                best_type = task_type
        if best_score >= 0.45:
            return best_type
    except Exception:
        logger.debug("Semantic task classification unavailable", exc_info=True)
    return None
