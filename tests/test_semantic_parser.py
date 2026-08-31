"""Tests for semantic intent parser (Priority 2)."""

from __future__ import annotations

import pytest

from app.commands.intent_models import IntentType
from app.commands.intent_parser_v2 import HashEmbedder, SemanticIntentParser
from app.conversation.command_engine import ConversationCommandEngine
from app.schemas.session import RepairSessionContext
from app.tools.registry import ToolRegistry


@pytest.fixture
def parser() -> SemanticIntentParser:
    return SemanticIntentParser(embedder=HashEmbedder())


@pytest.fixture
def semantic_engine() -> ConversationCommandEngine:
    return ConversationCommandEngine(
        intent_parser=SemanticIntentParser(embedder=HashEmbedder()),
        tool_registry=ToolRegistry(),
    )


def test_parse_open_3utools(parser: SemanticIntentParser) -> None:
    result = parser.parse("Aprimi 3uTools")
    assert result.intent == IntentType.OPEN_APPLICATION
    assert result.tool_id is not None
    assert "3utools" in result.tool_id.lower()
    assert result.confidence > 0.8


def test_parse_open_borneo(parser: SemanticIntentParser) -> None:
    result = parser.parse("Apri Borneo")
    assert result.intent in {IntentType.OPEN_APPLICATION, IntentType.CLARIFY}
    if result.intent == IntentType.OPEN_APPLICATION:
        assert result.tool_id is not None
        assert "borneo" in result.tool_id.lower()


def test_parse_ambiguous(parser: SemanticIntentParser) -> None:
    result = parser.parse("Apri il programma")
    assert result.intent == IntentType.CLARIFY
    assert result.options is not None
    assert len(result.options) > 0


def test_parse_unknown(parser: SemanticIntentParser) -> None:
    result = parser.parse("Raccontami una barzelletta")
    assert result.intent == IntentType.UNKNOWN


@pytest.mark.parametrize(
    ("text", "expected_intent"),
    [
        ("Apri 3uTools", IntentType.OPEN_APPLICATION),
        ("Avvia alpilab check", IntentType.OPEN_APPLICATION),
        ("open 3utools", IntentType.OPEN_APPLICATION),
        ("lancia termocamera", IntentType.OPEN_APPLICATION),
        ("Apri multimetro", IntentType.OPEN_APPLICATION),
        ("fai un test", IntentType.RUN_DIAGNOSTIC),
        ("diagnostica", IntentType.RUN_DIAGNOSTIC),
        ("controlla", IntentType.RUN_DIAGNOSTIC),
        ("chiudi 3utools", IntentType.CLOSE_APPLICATION),
    ],
)
def test_parse_common_commands(
    parser: SemanticIntentParser,
    text: str,
    expected_intent: IntentType,
) -> None:
    result = parser.parse(text)
    assert result.intent == expected_intent
    assert result.confidence >= SemanticIntentParser.CLARIFY_THRESHOLD


def test_tool_registry_get_all_tools() -> None:
    registry = ToolRegistry()
    tools = registry.get_all_tools()
    assert len(tools) >= 8
    ids = {tool["id"] for tool in tools}
    assert "3utools" in ids
    assert "windows.3utools.open" in ids


@pytest.mark.asyncio
async def test_semantic_command_engine_clarification(
    semantic_engine: ConversationCommandEngine,
) -> None:
    session = RepairSessionContext(repair_session_id="repair-001")
    result = await semantic_engine.process_user_input(
        "Apri il programma",
        session,
        session_id="repair-001",
        device_id="pc-1",
    )
    assert result["type"] == "clarification"
    assert "Quale intendi" in result["message"]


@pytest.mark.asyncio
async def test_semantic_command_engine_conversation(
    semantic_engine: ConversationCommandEngine,
) -> None:
    session = RepairSessionContext(repair_session_id="repair-001")
    result = await semantic_engine.process_user_input(
        "Raccontami una barzelletta",
        session,
        session_id="repair-001",
        device_id="pc-1",
    )
    assert result["type"] == "conversation"
    assert result["message"]
