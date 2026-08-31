"""Tests for diagnostic workflow engine (Priority 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.diagnostics.workflow_engine import (
    DiagnosticWorkflow,
    DiagnosticWorkflowError,
)
from app.schemas.repair import Device


@pytest.fixture
def iphone_device() -> Device:
    return Device(id="iphone-13-1", model="iPhone 13", brand="Apple")


def test_workflow_suggests_first_test(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)

    rec = workflow.next_step(current_symptoms=["display_broken"])

    assert rec.next_test is not None
    assert rec.next_test.id in ["visual_inspection", "test_display_cable"]
    assert rec.estimated_time_min >= 1


def test_workflow_no_repeat_tests(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)

    workflow.record_test_result("visual_inspection", True)

    rec = workflow.next_step(current_symptoms=["display_broken"])
    assert rec.next_test is not None
    assert rec.next_test.id != "visual_inspection"


def test_workflow_confidence_update(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)

    initial_conf = workflow._calculate_final_confidence()
    workflow.record_test_result("visual_inspection", True)
    updated_conf = workflow._calculate_final_confidence()

    assert updated_conf > initial_conf


def test_workflow_all_tests_completed(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)

    workflow.record_test_result("visual_inspection", True)
    workflow.record_test_result("test_display_cable", False)

    rec = workflow.next_step(current_symptoms=["display_broken"])
    assert rec.next_test is None
    assert "eseguiti" in rec.reasoning.lower()


def test_workflow_duplicate_test_raises(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)
    workflow.record_test_result("visual_inspection", True)

    with pytest.raises(DiagnosticWorkflowError):
        workflow.record_test_result("visual_inspection", False)


def test_workflow_loads_tree_from_json(tmp_path: Path, iphone_device: Device) -> None:
    tree = {
        "device": "iPhone 13",
        "initial_symptoms": ["no_charge"],
        "decision_trees": {
            "no_charge": {
                "tests": [
                    {
                        "id": "charge_port_inspection",
                        "label": "Ispezione porta ricarica",
                        "description": "Controlla sporco e danni",
                        "duration_sec": 90,
                        "risk_level": "low",
                    }
                ],
                "diagnosis_flow": {
                    "if_port_damaged": "charge_port_replacement",
                    "confidence_score": 0.85,
                },
            }
        },
    }
    (tmp_path / "iphone_13.json").write_text(json.dumps(tree), encoding="utf-8")

    workflow = DiagnosticWorkflow(iphone_device, trees_dir=tmp_path)
    rec = workflow.next_step(current_symptoms=["no_charge"])

    assert rec.next_test is not None
    assert rec.next_test.id == "charge_port_inspection"


def test_workflow_battery_symptom_tests(iphone_device: Device) -> None:
    workflow = DiagnosticWorkflow(iphone_device)

    rec = workflow.next_step(current_symptoms=["battery_drain"])

    assert rec.next_test is not None
    assert rec.next_test.id == "battery_health_check"
