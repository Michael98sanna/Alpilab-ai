"""Tests for iPhone panic log analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from pc_agent.tools.iphone_panic.analyzer import IPhonePanicAnalyzer
from pc_agent.tools.iphone_panic.parser import IPhonePanicParser

FIXTURE = Path("tests/fixtures/panic-full-sample.ips")


@pytest.mark.asyncio
async def test_analyze_smc_sensor() -> None:
    parser = IPhonePanicParser()
    doc = await parser.parse_file(str(FIXTURE))
    assert doc is not None

    analyzer = IPhonePanicAnalyzer()
    findings = analyzer.analyze(doc)

    assert findings.panic_type == "hardware_flex"
    assert findings.estimated_confidence >= 0.8
    assert any(match.rule_id == "smc_sensor_0x800" for match in findings.rule_matches)


def test_analyzer_loads_rules() -> None:
    analyzer = IPhonePanicAnalyzer()
    assert len(analyzer.rules) > 0
    assert "smc_sensor_0x800" in analyzer.rules
