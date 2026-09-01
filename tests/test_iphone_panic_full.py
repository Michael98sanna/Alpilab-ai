"""End-to-end tests for iPhone panic parser + analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from pc_agent.tools.iphone_panic.analyzer import IPhonePanicAnalyzer
from pc_agent.tools.iphone_panic.parser import IPhonePanicParser

FIXTURE = Path("tests/fixtures/panic-full-sample.ips")


@pytest.mark.asyncio
async def test_full_pipeline() -> None:
    parser = IPhonePanicParser()
    doc = await parser.parse_file(str(FIXTURE))

    assert doc is not None
    assert doc.metadata.bug_type == "210"
    assert "SMC PANIC" in doc.payload.panic_string

    analyzer = IPhonePanicAnalyzer()
    findings = analyzer.analyze(doc)

    assert findings.panic_type != "unknown"
    assert len(findings.rule_matches) > 0
    assert findings.estimated_confidence > 0.0


@pytest.mark.asyncio
async def test_parser_invalid_file() -> None:
    parser = IPhonePanicParser()
    doc = await parser.parse_file("/nonexistent.ips")
    assert doc is None


def test_analyzer_loads_rules() -> None:
    analyzer = IPhonePanicAnalyzer()
    assert len(analyzer.rules) > 0
    assert "smc_sensor_0x800" in analyzer.rules
