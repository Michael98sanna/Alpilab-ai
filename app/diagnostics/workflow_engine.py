"""Diagnostic workflow engine with decision trees and Bayesian confidence."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.repair import Device

logger = logging.getLogger(__name__)

TREES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "diagnostic_trees"


class DiagnosticTest(BaseModel):
    """A single diagnostic step suggested by the workflow."""

    id: str
    label: str
    description: str
    duration_sec: int
    risk_level: str


class DiagnosticRecommendation(BaseModel):
    """Next-step recommendation for a repair session."""

    next_test: DiagnosticTest | None = None
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    estimated_time_min: int = 0


class DiagnosticWorkflowError(Exception):
    """Raised when workflow operations fail."""


class DiagnosticWorkflow:
    """
    Orchestrates diagnostic workflow per device.

    Loads decision trees from ``data/diagnostic_trees/``, tracks completed tests
    (anti-loop), and updates diagnosis hypotheses with a simplified Bayesian update.
    """

    POSITIVE_MULTIPLIER = 1.2
    NEGATIVE_MULTIPLIER = 0.7

    def __init__(
        self,
        device: Device,
        *,
        trees_dir: Path | None = None,
    ) -> None:
        self.device = device
        self.completed_tests: dict[str, bool] = {}
        self.hypothesis_confidence: dict[str, float] = {}
        self._trees_dir = trees_dir or TREES_DIR
        self.tree = self._load_tree(device.model)

    def next_step(self, current_symptoms: list[str]) -> DiagnosticRecommendation:
        """
        Suggest the next diagnostic test.

        Filters out completed tests and returns the highest-priority remaining step.
        """
        available_tests = [
            test
            for test in self._get_tests_for_symptoms(current_symptoms)
            if test["id"] not in self.completed_tests
        ]

        if not available_tests:
            return DiagnosticRecommendation(
                reasoning="Tutti i test rilevanti sono stati eseguiti.",
                confidence_score=self._calculate_final_confidence(),
                estimated_time_min=0,
            )

        best_test = available_tests[0]
        base_confidence = self._diagnosis_flow_for_symptoms(current_symptoms).get(
            "confidence_score",
            0.70,
        )
        confidence = max(self._calculate_final_confidence(), float(base_confidence))

        return DiagnosticRecommendation(
            next_test=DiagnosticTest(**best_test),
            reasoning=f"Test suggerito: {best_test['label']}",
            confidence_score=min(confidence, 1.0),
            estimated_time_min=max(best_test["duration_sec"] // 60, 1),
        )

    def record_test_result(self, test_id: str, result: bool) -> None:
        """Record a completed test and update hypothesis confidence."""
        if not test_id:
            raise ValueError("test_id is required")

        if test_id in self.completed_tests:
            raise DiagnosticWorkflowError(f"Test {test_id!r} already recorded")

        self._ensure_hypotheses_initialized()
        self.completed_tests[test_id] = result
        self._update_hypothesis_confidence(test_id, result)

    def _load_tree(self, device_model: str) -> dict[str, Any]:
        """Load a decision tree JSON file for the device model."""
        path = self._trees_dir / self._model_to_filename(device_model)
        if not path.is_file():
            logger.warning("Diagnostic tree not found for model %s at %s", device_model, path)
            return {
                "device": device_model,
                "initial_symptoms": [],
                "decision_tree": {},
            }

        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise DiagnosticWorkflowError(
                f"Invalid diagnostic tree JSON: {path}"
            ) from exc

    @staticmethod
    def _model_to_filename(device_model: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "_", device_model.lower()).strip("_")
        return f"{slug}.json"

    def _get_tests_for_symptoms(self, symptoms: list[str]) -> list[dict[str, Any]]:
        """Return tests relevant to the active symptoms."""
        trees = self.tree.get("decision_trees")
        if isinstance(trees, dict) and trees:
            merged: dict[str, dict[str, Any]] = {}
            for symptom in symptoms:
                node = trees.get(symptom, {})
                for test in node.get("tests", []):
                    merged[test["id"]] = test
            return list(merged.values())

        decision_tree = self.tree.get("decision_tree", {})
        tree_symptom = decision_tree.get("symptom")
        if not symptoms or tree_symptom in symptoms:
            return list(decision_tree.get("tests", []))
        return []

    def _diagnosis_flow_for_symptoms(self, symptoms: list[str]) -> dict[str, Any]:
        trees = self.tree.get("decision_trees")
        if isinstance(trees, dict) and symptoms:
            for symptom in symptoms:
                flow = trees.get(symptom, {}).get("diagnosis_flow")
                if isinstance(flow, dict):
                    return flow

        decision_tree = self.tree.get("decision_tree", {})
        flow = decision_tree.get("diagnosis_flow")
        return flow if isinstance(flow, dict) else {}

    def _ensure_hypotheses_initialized(self) -> None:
        if self.hypothesis_confidence:
            return

        flow = self._diagnosis_flow_for_symptoms(self.tree.get("initial_symptoms", []))
        if not flow:
            decision_tree = self.tree.get("decision_tree", {})
            flow = decision_tree.get("diagnosis_flow", {})

        base = float(flow.get("confidence_score", 0.5))
        for key, value in flow.items():
            if key == "confidence_score":
                continue
            if isinstance(value, str):
                self.hypothesis_confidence[value] = base

    def _update_hypothesis_confidence(self, test_id: str, result: bool) -> None:
        """Simplified Bayesian-style update for diagnosis hypotheses."""
        _ = test_id
        multiplier = self.POSITIVE_MULTIPLIER if result else self.NEGATIVE_MULTIPLIER

        for diagnosis in self.hypothesis_confidence:
            self.hypothesis_confidence[diagnosis] *= multiplier

        max_conf = max(self.hypothesis_confidence.values()) if self.hypothesis_confidence else 1.0
        if max_conf > 0:
            for diagnosis in self.hypothesis_confidence:
                self.hypothesis_confidence[diagnosis] /= max_conf

    def _calculate_final_confidence(self) -> float:
        """Mean confidence across active diagnosis hypotheses."""
        if not self.hypothesis_confidence:
            return 0.0
        return sum(self.hypothesis_confidence.values()) / len(self.hypothesis_confidence)
