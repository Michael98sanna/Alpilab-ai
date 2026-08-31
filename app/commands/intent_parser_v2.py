"""Semantic + rule-based natural language intent parser."""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

import numpy as np

from app.commands.intent_models import IntentOption, IntentResult, IntentType
from app.tools.registry import ToolRegistry, default_tool_registry

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    """Minimal embedding interface used by the semantic parser."""

    def encode(self, text: str, *, convert_to_tensor: bool = False) -> np.ndarray:
        ...


class HashEmbedder:
    """Deterministic lightweight embedder for tests and offline fallback."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode(self, text: str, *, convert_to_tensor: bool = False) -> np.ndarray:
        tokens = re.findall(r"\w+", text.lower())
        vector = np.zeros(self.dimensions, dtype=np.float64)
        for token in tokens:
            vector[hash(token) % self.dimensions] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector


class LazySentenceTransformerEmbedder:
    """Lazy-loaded sentence-transformers backend."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, text: str, *, convert_to_tensor: bool = False) -> np.ndarray:
        model = self._get_model()
        embedding = model.encode(text, convert_to_tensor=convert_to_tensor)
        if convert_to_tensor:
            return embedding
        return np.asarray(embedding, dtype=np.float64)


def default_embedder() -> Embedder:
    """Prefer sentence-transformers when installed; otherwise hash fallback."""
    try:
        import sentence_transformers  # noqa: F401

        return LazySentenceTransformerEmbedder()
    except ImportError:
        logger.info("sentence-transformers not installed; using HashEmbedder")
        return HashEmbedder()


class SemanticIntentParser:
    """
    Parser rule-based + semantic matching for natural commands.

    Uses sentence-transformers when available; falls back to a deterministic
    hash embedder. Rule-based matching runs first for known open/close verbs.
    """

    CONFIDENCE_THRESHOLD = 0.70
    CLARIFY_THRESHOLD = 0.55
    RULE_MATCH_CONFIDENCE = 0.95

    _OPEN_VERB = re.compile(
        r"^(?:apri|aprimi|avvia|lancia|open|launch|start|"
        r"puoi\s+aprire|puoi\s+avviare)\s+(?:il\s+|l'|la\s+)?(.+?)\.?$",
        re.I,
    )
    _CLOSE_VERB = re.compile(r"^(?:chiudi|close)\s+(?:il\s+|l'|la\s+)?(.+)$", re.I)

    _APP_ALIASES: dict[str, str] = {
        "3utools": "windows.3utools.open",
        "3u tools": "windows.3utools.open",
        "3 u tools": "windows.3utools.open",
        "alpilab check": "windows.alpilab_check.open",
        "alpilab_check": "windows.alpilab_check.open",
        "alpilabcheck": "windows.alpilab_check.open",
        "borneo": "windows.borneo.open",
        "borneo schematics": "windows.borneo.open",
        "zxw": "zxw",
        "termocamera": "windows.thermal_camera.open",
        "thermal camera": "windows.thermal_camera.open",
        "multimetro": "multimeter",
        "microscopio": "windows.microscope.open",
        "microscope": "windows.microscope.open",
        "alimentatore": "power_supply",
    }

    _AMBIGUOUS_TARGETS = frozenset(
        {
            "programma",
            "il programma",
            "applicazione",
            "l applicazione",
            "l'applicazione",
            "quello",
            "quello per iphone",
        }
    )

    _CONVERSATION_HINTS = (
        "barzelletta",
        "raccontami",
        "come stai",
        "che tempo",
        "grazie",
        "ciao",
    )

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        tool_registry: ToolRegistry | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.tool_registry = tool_registry or default_tool_registry
        self.embedder: Embedder = embedder or default_embedder()
        self.command_templates = self._build_templates()
        self._tool_catalog = self._build_tool_catalog()
        self._catalog_embeddings = self._precompute_catalog_embeddings()

    def _build_templates(self) -> dict[str, list[str]]:
        return {
            "open_application": [
                "aprimi {app}",
                "apri {app}",
                "avvia {app}",
                "lancia {app}",
                "apri il {app}",
                "open {app}",
            ],
            "close_application": [
                "chiudi {app}",
                "chiudi il {app}",
                "close {app}",
            ],
            "run_diagnostic": [
                "fai un test",
                "diagnostica",
                "controlla",
                "run diagnostic",
            ],
        }

    def _build_tool_catalog(self) -> list[dict[str, str]]:
        catalog: dict[str, dict[str, str]] = {}
        for tool in self.tool_registry.get_all_tools():
            catalog[tool["id"]] = tool
        return list(catalog.values())

    def _precompute_catalog_embeddings(self) -> dict[str, np.ndarray]:
        embeddings: dict[str, np.ndarray] = {}
        for item in self._tool_catalog:
            text = f"{item['label']} {item['description']}"
            embeddings[item["id"]] = self.embedder.encode(text)
        return embeddings

    def parse(self, user_text: str) -> IntentResult:
        """
        Parse natural language input into an ``IntentResult``.

        1. Normalize input
        2. Rule-based fast path (open/close/diagnostic/ambiguous)
        3. Semantic similarity against registered tools
        4. Thresholds for match, clarify, or unknown
        """
        user_text_clean = user_text.strip()
        if not user_text_clean:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Input vuoto",
            )

        normalized = self._normalize(user_text_clean)

        rule_result = self._parse_with_rules(normalized, user_text_clean)
        if rule_result is not None:
            return rule_result

        if any(hint in normalized for hint in self._CONVERSATION_HINTS):
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.2,
                reasoning="Rilevato contenuto conversazionale",
            )

        return self._parse_with_semantics(normalized)

    def _normalize(self, text: str) -> str:
        value = text.strip().lower()
        value = value.replace("3u tools", "3utools")
        value = value.replace("3 u tools", "3utools")
        value = value.replace("alpilab check", "alpilab_check")
        value = value.replace("alpilabcheck", "alpilab_check")
        value = re.sub(r"\s+", " ", value)
        return value.rstrip("?").strip()

    def _parse_with_rules(
        self,
        normalized: str,
        raw_text: str,
    ) -> IntentResult | None:
        for phrase in self.command_templates["run_diagnostic"]:
            if normalized == phrase or normalized.startswith(f"{phrase} "):
                return IntentResult(
                    intent=IntentType.RUN_DIAGNOSTIC,
                    confidence=self.RULE_MATCH_CONFIDENCE,
                    reasoning=f"Matched diagnostic phrase '{phrase}'",
                )

        close_match = self._CLOSE_VERB.match(normalized)
        if close_match:
            target = self._normalize(close_match.group(1))
            tool_id = self._resolve_alias(target)
            return IntentResult(
                intent=IntentType.CLOSE_APPLICATION,
                tool_id=tool_id,
                confidence=self.RULE_MATCH_CONFIDENCE,
                reasoning=f"Matched close command for '{target}'",
            )

        if normalized in self._AMBIGUOUS_TARGETS or normalized.endswith(" programma"):
            return self._clarify_from_semantics(normalized, reason="Target ambiguo")

        open_match = self._OPEN_VERB.match(normalized)
        if open_match:
            target = self._normalize(open_match.group(1))
            if target in self._AMBIGUOUS_TARGETS or "quello" in target:
                return self._clarify_from_semantics(normalized, reason="Target ambiguo")

            tool_id = self._resolve_alias(target)
            if tool_id:
                return IntentResult(
                    intent=IntentType.OPEN_APPLICATION,
                    tool_id=tool_id,
                    confidence=self.RULE_MATCH_CONFIDENCE,
                    reasoning=f"Rule matched open target '{target}'",
                )

        if normalized in self._APP_ALIASES:
            tool_id = self._APP_ALIASES[normalized]
            return IntentResult(
                intent=IntentType.OPEN_APPLICATION,
                tool_id=tool_id,
                confidence=self.RULE_MATCH_CONFIDENCE,
                reasoning=f"Exact alias match '{normalized}'",
            )

        return None

    def _resolve_alias(self, target: str) -> str | None:
        if target in self._APP_ALIASES:
            return self._APP_ALIASES[target]
        compact = target.replace(" ", "")
        if compact in self._APP_ALIASES:
            return self._APP_ALIASES[compact]
        for tool in self._tool_catalog:
            if target == tool["id"] or target == tool["label"].lower():
                return tool["id"]
        return None

    def _parse_with_semantics(self, normalized: str) -> IntentResult:
        if not self._tool_catalog:
            return IntentResult(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning="Nessun tool registrato",
            )

        user_embedding = self.embedder.encode(normalized)
        scores: dict[str, float] = {}
        for item in self._tool_catalog:
            tool_embedding = self._catalog_embeddings[item["id"]]
            scores[item["id"]] = self._cosine_similarity(user_embedding, tool_embedding)

        sorted_scores = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
        top_tool_id, top_confidence = sorted_scores[0]

        if top_confidence >= self.CONFIDENCE_THRESHOLD:
            return IntentResult(
                intent=IntentType.OPEN_APPLICATION,
                tool_id=top_tool_id,
                confidence=float(top_confidence),
                reasoning=(
                    f"Matched '{top_tool_id}' con confidence {top_confidence:.2f}"
                ),
            )

        if top_confidence >= self.CLARIFY_THRESHOLD:
            return self._build_clarify_result(sorted_scores[:3], top_confidence)

        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=float(top_confidence),
            reasoning=(
                f"Confidence troppo bassa: {top_confidence:.2f} "
                f"< {self.CONFIDENCE_THRESHOLD}"
            ),
        )

    def _clarify_from_semantics(self, normalized: str, *, reason: str) -> IntentResult:
        if not self._tool_catalog:
            return IntentResult(
                intent=IntentType.CLARIFY,
                confidence=self.CLARIFY_THRESHOLD,
                options=[],
                reasoning=reason,
            )
        user_embedding = self.embedder.encode(normalized)
        scores = [
            (
                item["id"],
                self._cosine_similarity(user_embedding, self._catalog_embeddings[item["id"]]),
            )
            for item in self._tool_catalog
        ]
        scores.sort(key=lambda pair: pair[1], reverse=True)
        top_confidence = scores[0][1] if scores else self.CLARIFY_THRESHOLD
        return self._build_clarify_result(scores[:3], max(top_confidence, self.CLARIFY_THRESHOLD), reason=reason)

    def _build_clarify_result(
        self,
        ranked: list[tuple[str, float]],
        confidence: float,
        *,
        reason: str = "Ambiguo tra opzioni",
    ) -> IntentResult:
        options = [
            IntentOption(
                tool_id=tool_id,
                label=self.tool_registry.get_tool_label(tool_id),
                confidence=float(score),
            )
            for tool_id, score in ranked
        ]
        return IntentResult(
            intent=IntentType.CLARIFY,
            confidence=float(confidence),
            options=options,
            reasoning=f"{reason} ({len(options)} opzioni)",
        )

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)
