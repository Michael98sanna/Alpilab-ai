"""Tests for iPhone panic log parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from pc_agent.tools.iphone_panic.parser import IPhonePanicParser

FIXTURE = Path("tests/fixtures/panic-full-sample.ips")


@pytest.mark.asyncio
async def test_parse_sample_ips() -> None:
    parser = IPhonePanicParser()
    doc = await parser.parse_file(str(FIXTURE))

    assert doc is not None
    assert doc.metadata.bug_type == "210"
    assert "SMC PANIC" in doc.payload.panic_string
    assert len(doc.file_hash) == 64


@pytest.mark.asyncio
async def test_extract_panic_signature() -> None:
    parser = IPhonePanicParser()
    signature = parser._extract_panic_signature("panic(cpu 3): SMC PANIC - 0x800")
    assert signature is not None
    assert "SMC PANIC" in signature


@pytest.mark.asyncio
async def test_parse_invalid_file() -> None:
    parser = IPhonePanicParser()
    doc = await parser.parse_file("/nonexistent/file.ips")
    assert doc is None
