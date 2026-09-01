"""Apply YAML diagnostic rules to parsed panic logs."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .models import AnalysisFindings, PanicLogDocument, RuleMatch

logger = logging.getLogger(__name__)

DEFAULT_RULES_DIR = Path(__file__).resolve().parent / "rules"


class IPhonePanicAnalyzer:
    """Analyze PanicLogDocument using YAML rules."""

    def __init__(self, rules_dir: str | Path | None = None) -> None:
        self.rules_dir = Path(rules_dir) if rules_dir else DEFAULT_RULES_DIR
        self.rules = self._load_rules()
        logger.info("Loaded %d iPhone panic rules", len(self.rules))

    def analyze(self, doc: PanicLogDocument) -> AnalysisFindings:
        """Apply all rules and build aggregated findings."""
        rule_matches: list[RuleMatch] = []
        dominant_component: str | None = None
        dominant_severity = "low"
        max_confidence = 0.0
        panic_type = "unknown"
        panic_signature = self._extract_signature(doc)

        for rule_id, rule in self.rules.items():
            match = self._match_rule(rule_id, rule, doc)
            if match.matched:
                rule_matches.append(match)
                if match.confidence >= max_confidence:
                    max_confidence = match.confidence
                    dominant_component = match.component
                    dominant_severity = match.severity
                    panic_type = str(rule.get("category", "unknown"))

        findings = AnalysisFindings(
            panic_type=panic_type,
            panic_signature=panic_signature,
            rule_matches=rule_matches,
            dominant_component=dominant_component,
            estimated_severity=dominant_severity,
            estimated_confidence=max_confidence,
            raw_data={
                "bug_type": doc.metadata.bug_type,
                "model": doc.metadata.model_code,
                "matches": len(rule_matches),
            },
        )
        logger.info(
            "Analysis complete: %s (confidence %.2f)",
            findings.panic_type,
            findings.estimated_confidence,
        )
        return findings

    def _load_rules(self) -> dict[str, dict[str, Any]]:
        try:
            index_file = self.rules_dir / "index.yaml"
            with open(index_file, encoding="utf-8") as handle:
                index = yaml.safe_load(handle) or {}
            rules: dict[str, dict[str, Any]] = {}
            for rule in index.get("rules", []):
                rules[str(rule["id"])] = rule
            return rules
        except Exception as exc:
            logger.error("Error loading rules: %s", exc)
            return {}

    def _match_rule(
        self,
        rule_id: str,
        rule: dict[str, Any],
        doc: PanicLogDocument,
    ) -> RuleMatch:
        triggers = rule.get("triggers", {})
        panic_str = doc.payload.panic_string.lower()
        matched = False
        confidence = 0.0
        error_code = self._extract_error_code(doc.payload.panic_string)

        contains_list = triggers.get("panic_string_contains") or []
        if contains_list:
            matches_count = sum(
                1 for substring in contains_list if substring.lower() in panic_str
            )
            if matches_count > 0:
                matched = True
                confidence = min(1.0, matches_count / len(contains_list))

        if not matched:
            exception_types = triggers.get("exception_type") or []
            if doc.metadata.bug_type in exception_types:
                matched = True
                confidence = float(rule.get("confidence_base", 0.5))

        if not matched:
            panic_types = triggers.get("panic_type") or []
            if doc.metadata.bug_type in panic_types:
                matched = True
                confidence = float(rule.get("confidence_base", 0.5))

        if matched:
            confidence = max(confidence, float(rule.get("confidence_base", 0.5)))

        return RuleMatch(
            rule_id=rule_id,
            rule_name=str(rule.get("name", rule_id)),
            matched=matched,
            confidence=confidence if matched else 0.0,
            component=rule.get("component"),
            error_code=error_code,
            severity=str(rule.get("severity", "low")),
            details={
                "category": rule.get("category"),
                "description": rule.get("description"),
            },
        )

    def _extract_signature(self, doc: PanicLogDocument) -> str | None:
        patterns = [
            r"(SMC PANIC[^\n]*)",
            r"(NAND[^\n]*)",
            r"(kernel panic[^\n]*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, doc.payload.panic_string, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:100]
        return None

    def _extract_error_code(self, panic_string: str) -> str | None:
        match = re.search(r"(0x[a-fA-F0-9]+)", panic_string)
        return match.group(1) if match else None
