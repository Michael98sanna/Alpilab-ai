"""Tests for SEARCH → SELECTION → DETAIL Alpilab Check conversation flow."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.agent.payloads import AgentCapabilities, ResultEnvelope
from app.agent.registry import RegisteredAgent, agent_registry
from app.commands.natural_language_parser import NaturalLanguageCommandParser, ParseOutcome
from app.conversation.alpilab_check_context import (
    ProductSearchContext,
    ProductSearchItem,
    apply_product_search_context,
    build_product_search_context,
    format_product_label,
)
from app.conversation.alpilab_check_followup import (
    FollowUpOutcome,
    resolve_product_followup,
)
from app.conversation.alpilab_check_messages import (
    format_disambiguation_message,
    format_get_product_response,
    format_search_products_response,
    format_selection_confirmation,
)
from app.conversation.natural_language_service import NaturalLanguageCommandService
from app.realtime.session_manager import RealtimeSessionManager


@pytest.fixture(autouse=True)
def reset_state() -> None:
    agent_registry.clear()
    from app.realtime import session_manager as sm

    sm.realtime_manager._sessions.clear()
    sm.realtime_manager._ws_connections.clear()
    sm.realtime_manager._event_log.clear()


def _s24_items() -> list[ProductSearchItem]:
    return [
        ProductSearchItem(
            id="tech-s24-5g",
            brand="Samsung",
            model="S24 5G",
            model_code="SM-S921",
        ),
        ProductSearchItem(
            id="tech-s24-plus",
            brand="Samsung",
            model="S24+",
            model_code="SM-S926",
        ),
        ProductSearchItem(
            id="tech-s24-ultra",
            brand="Samsung",
            model="S24 Ultra",
            model_code="SM-S928",
        ),
        ProductSearchItem(
            id="tech-s24-fe",
            brand="Samsung",
            model="S24 FE 5G",
            model_code="SM-S721",
        ),
    ]


def _s24_context(*, awaiting: bool = True) -> ProductSearchContext:
    items = _s24_items()
    if awaiting:
        return ProductSearchContext(
            items=items,
            created_at=datetime.now(timezone.utc),
            awaiting_selection=True,
            selected_index=None,
            selected_product_id=None,
        )
    return ProductSearchContext(
        items=items,
        created_at=datetime.now(timezone.utc),
        awaiting_selection=False,
        selected_index=2,
        selected_product_id="tech-s24-ultra",
    )


def _sample_context(*, awaiting: bool = True) -> ProductSearchContext:
    return ProductSearchContext(
        items=[
            ProductSearchItem(
                id="prod-1",
                brand="Apple",
                model="iPhone 14",
                model_code="A2882",
            ),
            ProductSearchItem(
                id="prod-2",
                brand="Apple",
                model="iPhone 15",
                model_code="A3090",
            ),
        ],
        created_at=datetime.now(timezone.utc),
        awaiting_selection=awaiting,
        selected_index=None if awaiting else 0,
        selected_product_id=None if awaiting else "prod-1",
    )


def _register_agent(session_id: str, agent_id: str = "agent-test-01") -> None:
    agent_registry.register(
        RegisteredAgent(
            agent_id=agent_id,
            session_id=session_id,
            agent_name="PC",
            platform="windows",
            agent_version="0.4.0",
            capabilities=AgentCapabilities(
                safe_test=True,
                windows_apps=True,
                alpilab_check=True,
            ),
            status="ONLINE",
            connected_at=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            send_json=lambda x: None,
        )
    )


# --- SEARCH ---


def test_search_zero_results() -> None:
    assert (
        format_search_products_response({"items": []})
        == "Non ho trovato prodotti nel listino per questa ricerca."
    )
    assert build_product_search_context({"items": []}) is None


def test_search_one_result_selects_without_listino() -> None:
    payload = {
        "items": [
            {
                "id": "only-ultra",
                "brand": "Samsung",
                "model": "S24 Ultra",
                "model_code": "SM-S928",
                "services": [{"name": "Batteria", "price": 65.7}],
            }
        ]
    }
    ctx = build_product_search_context(payload)
    assert ctx is not None
    assert ctx.awaiting_selection is False
    assert ctx.selected_index == 0
    assert ctx.selected_product_id == "only-ultra"
    msg = format_search_products_response(payload, context=ctx)
    assert msg == "Ho trovato Samsung S24 Ultra. Cosa vuoi sapere?"
    assert "Batteria" not in msg
    assert "65" not in msg
    assert "only-ultra" not in msg


def test_search_multi_results_asks_selection() -> None:
    payload = {
        "items": [
            {
                "id": item.id,
                "brand": item.brand,
                "model": item.model,
                "model_code": item.model_code,
            }
            for item in _s24_items()
        ]
    }
    ctx = build_product_search_context(payload)
    assert ctx is not None
    assert ctx.awaiting_selection is True
    assert ctx.selected_index is None
    assert ctx.selected_product_id is None
    msg = format_search_products_response(payload, context=ctx)
    assert msg.startswith("Ho trovato 4 modelli:")
    assert "1. Samsung S24 5G" in msg
    assert "3. Samsung S24 Ultra" in msg
    assert msg.strip().endswith("Quale intendi?")
    for item in ctx.items:
        assert item.id not in msg


# --- SELECTION ---


@pytest.mark.parametrize(
    ("text", "product_id", "label"),
    [
        ("S24 Ultra", "tech-s24-ultra", "Samsung S24 Ultra"),
        ("il terzo", "tech-s24-ultra", "Samsung S24 Ultra"),
        ("3", "tech-s24-ultra", "Samsung S24 Ultra"),
        ("e il secondo?", "tech-s24-plus", "Samsung S24+"),
        ("e S24+?", "tech-s24-plus", "Samsung S24+"),
        ("e per S24+?", "tech-s24-plus", "Samsung S24+"),
    ],
)
def test_selection_without_get_product(text: str, product_id: str, label: str) -> None:
    ctx = _s24_context(awaiting=True)
    result = resolve_product_followup(text, ctx)
    assert result.outcome == FollowUpOutcome.SELECTION
    assert result.intent is None
    assert result.message == f"Perfetto, {label}."
    assert ctx.selected_product_id == product_id
    assert ctx.awaiting_selection is False


def test_selection_change_model_without_get_product() -> None:
    ctx = _s24_context(awaiting=False)
    assert ctx.selected_product_id == "tech-s24-ultra"
    result = resolve_product_followup("e S24+?", ctx)
    assert result.outcome == FollowUpOutcome.SELECTION
    assert result.intent is None
    assert result.message == "Perfetto, Samsung S24+."
    assert ctx.selected_product_id == "tech-s24-plus"


def test_model_not_in_context_does_not_invent_id() -> None:
    ctx = _s24_context(awaiting=True)
    result = resolve_product_followup("e per iPhone 12?", ctx)
    assert result.outcome == FollowUpOutcome.CLARIFICATION
    assert result.intent is None
    assert ctx.selected_product_id is None
    assert "iphone 12" in (result.message or "").lower()


def test_ordinal_out_of_range_clarification() -> None:
    result = resolve_product_followup("il quarto", _sample_context())
    assert result.outcome == FollowUpOutcome.CLARIFICATION
    assert result.intent is None
    assert "quarto" in (result.message or "")


# --- DETAIL ---


@pytest.mark.parametrize(
    ("text", "focus"),
    [
        ("quanto costa la batteria?", "batteria"),
        ("quanto costa lo schermo?", "schermo"),
        ("e la batteria?", "batteria"),
        ("quali servizi ci sono?", "servizi"),
        ("quanto costa la riparazione?", "riparazione"),
        ("quanto costa la manodopera?", "manodopera"),
    ],
)
def test_detail_requests_get_product(text: str, focus: str) -> None:
    ctx = _s24_context(awaiting=False)
    result = resolve_product_followup(text, ctx)
    assert result.outcome == FollowUpOutcome.ACTION
    assert result.intent is not None
    assert result.intent.target == "alpilab_check.get_product"
    assert result.intent.parameters == {"product_id": "tech-s24-ultra"}
    assert result.detail_focus == focus


def test_detail_response_batteria_natural_copy() -> None:
    msg = format_get_product_response(
        {
            "id": "tech-s24-ultra",
            "brand": "Samsung",
            "model": "S24 Ultra",
            "services": [{"name": "Batteria", "price": 65.7}],
        },
        detail_focus="batteria",
        product_label="Samsung S24 Ultra",
    )
    assert msg == "La batteria per Samsung S24 Ultra costa €65,70."
    assert "batteria: Batteria" not in msg
    assert "Dettaglio prodotto" not in msg
    assert "tech-s24-ultra" not in msg


def test_detail_response_schermo() -> None:
    msg = format_get_product_response(
        {
            "id": "x",
            "brand": "Samsung",
            "model": "S24 Ultra",
            "services": [{"name": "Schermo", "price": 199}],
        },
        detail_focus="schermo",
        product_label="Samsung S24 Ultra",
    )
    assert msg == "Lo schermo per Samsung S24 Ultra costa €199,00."


def test_detail_missing_batteria() -> None:
    msg = format_get_product_response(
        {"id": "x", "brand": "Samsung", "model": "S24 Ultra", "services": []},
        detail_focus="batteria",
        product_label="Samsung S24 Ultra",
    )
    assert msg == "Non ho trovato il prezzo della batteria per Samsung S24 Ultra."


def test_detail_without_selection_asks_disambiguation() -> None:
    result = resolve_product_followup(
        "quanto costa la batteria?", _s24_context(awaiting=True)
    )
    assert result.outcome == FollowUpOutcome.CLARIFICATION
    assert result.intent is None
    assert "Quale intendi?" in (result.message or "")


# --- SELECTION + DETAIL same turn ---


@pytest.mark.parametrize(
    ("text", "product_id", "focus"),
    [
        ("quanto costa la batteria del terzo?", "tech-s24-ultra", "batteria"),
        ("quanto costa lo schermo del S24 Ultra?", "tech-s24-ultra", "schermo"),
        ("e per il secondo quanto costa la batteria?", "tech-s24-plus", "batteria"),
    ],
)
def test_selection_plus_detail_calls_get_product(
    text: str, product_id: str, focus: str
) -> None:
    ctx = _s24_context(awaiting=True)
    result = resolve_product_followup(text, ctx)
    assert result.outcome == FollowUpOutcome.ACTION
    assert result.intent is not None
    assert result.intent.parameters == {"product_id": product_id}
    assert result.detail_focus == focus
    assert ctx.selected_product_id == product_id
    assert result.message is None


# --- CONTEXT ---


def test_context_isolated_per_session() -> None:
    rt = RealtimeSessionManager()
    s1 = rt.create_session("session-a", seed_demo=False)
    s2 = rt.create_session("session-b", seed_demo=False)
    apply_product_search_context(
        s1,
        {"items": [{"id": "a1", "brand": "Apple", "model": "Phone"}]},
    )
    assert s2.product_search_context is None
    assert s1.product_search_context is not None
    assert s1.product_search_context.selected_product_id == "a1"


def test_empty_context_followup_no_match() -> None:
    assert resolve_product_followup("3", None).outcome == FollowUpOutcome.NO_MATCH
    assert resolve_product_followup("3", ProductSearchContext(items=[])).outcome == (
        FollowUpOutcome.NO_MATCH
    )


def test_format_selection_confirmation() -> None:
    item = ProductSearchItem(id="hid", brand="Samsung", model="S24 Ultra")
    assert format_selection_confirmation(item) == "Perfetto, Samsung S24 Ultra."
    assert format_product_label(item) == "Samsung S24 Ultra"


# --- Service: SELECTION must not call get_product ---


@pytest.mark.asyncio
async def test_selection_does_not_call_get_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation import natural_language_service as nls_mod
    from app.realtime import session_manager as sm_mod

    rt = RealtimeSessionManager()
    rt.create_session("repair-sel", seed_demo=False)
    _register_agent("repair-sel")
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    calls: list[tuple[str, dict]] = []

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        calls.append((tool_id, dict(arguments or {})))
        if tool_id == "alpilab_check.search_products":
            return ResultEnvelope(
                request_id="req-search",
                command_id="cmd-search",
                agent_id=agent_id,
                tool_id=tool_id,
                success=True,
                result={
                    "items": [
                        {
                            "id": item.id,
                            "brand": item.brand,
                            "model": item.model,
                            "model_code": item.model_code,
                        }
                        for item in _s24_items()
                    ]
                },
                timestamp="2026-01-01T00:00:00+00:00",
            )
        return ResultEnvelope(
            request_id="req-get",
            command_id="cmd-get",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={
                "id": arguments["product_id"],
                "brand": "Samsung",
                "model": "S24 Ultra",
                "services": [{"name": "Batteria", "price": 65.7}],
            },
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    service = NaturalLanguageCommandService()

    await service.handle_user_message("repair-sel", "device-1", "Cerca S24 nel listino")
    session = rt.get_session("repair-sel")
    assert session is not None
    assert session.product_search_context is not None
    assert session.product_search_context.awaiting_selection is True
    search_msg = [m for m in session.messages if m.role == "assistant"][-1].content
    assert "Quale intendi?" in search_msg
    assert "Batteria" not in search_msg
    assert calls == [
        ("alpilab_check.search_products", {"query": "s24", "limit": 20})
    ]

    await service.handle_user_message("repair-sel", "device-1", "S24 Ultra")
    assert session.product_search_context.selected_product_id == "tech-s24-ultra"
    assert all(c[0] != "alpilab_check.get_product" for c in calls)
    sel_msg = [m for m in session.messages if m.role == "assistant"][-1].content
    assert sel_msg == "Perfetto, Samsung S24 Ultra."
    assert "Batteria" not in sel_msg
    assert "[MOCK]" not in sel_msg

    await service.handle_user_message("repair-sel", "device-1", "quanto costa la batteria?")
    assert calls[-1] == (
        "alpilab_check.get_product",
        {"product_id": "tech-s24-ultra"},
    )
    detail_msg = [m for m in session.messages if m.role == "assistant"][-1].content
    assert detail_msg == "La batteria per Samsung S24 Ultra costa €65,70."


@pytest.mark.asyncio
async def test_change_selection_then_detail_uses_new_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation import natural_language_service as nls_mod
    from app.realtime import session_manager as sm_mod

    rt = RealtimeSessionManager()
    rt.create_session("repair-switch", seed_demo=False)
    _register_agent("repair-switch")
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    calls: list[tuple[str, dict]] = []

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        calls.append((tool_id, dict(arguments or {})))
        if tool_id == "alpilab_check.search_products":
            return ResultEnvelope(
                request_id="req-search",
                command_id="cmd-search",
                agent_id=agent_id,
                tool_id=tool_id,
                success=True,
                result={
                    "items": [
                        {"id": item.id, "brand": item.brand, "model": item.model}
                        for item in _s24_items()
                    ]
                },
                timestamp="2026-01-01T00:00:00+00:00",
            )
        return ResultEnvelope(
            request_id="req-get",
            command_id="cmd-get",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={
                "id": arguments["product_id"],
                "brand": "Samsung",
                "model": "S24+",
                "services": [{"name": "Batteria", "price": 55}],
            },
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    service = NaturalLanguageCommandService()
    await service.handle_user_message("repair-switch", "d1", "Cerca S24 nel listino")
    await service.handle_user_message("repair-switch", "d1", "S24 Ultra")
    await service.handle_user_message("repair-switch", "d1", "e S24+?")
    session = rt.get_session("repair-switch")
    assert session is not None
    assert session.product_search_context is not None
    assert session.product_search_context.selected_product_id == "tech-s24-plus"
    assert sum(1 for c in calls if c[0] == "alpilab_check.get_product") == 0

    await service.handle_user_message("repair-switch", "d1", "quanto costa la batteria?")
    assert calls[-1] == (
        "alpilab_check.get_product",
        {"product_id": "tech-s24-plus"},
    )


@pytest.mark.asyncio
async def test_single_result_search_no_auto_get_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation import natural_language_service as nls_mod
    from app.realtime import session_manager as sm_mod

    rt = RealtimeSessionManager()
    rt.create_session("repair-one", seed_demo=False)
    _register_agent("repair-one")
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)
    calls: list[str] = []

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        calls.append(tool_id)
        if tool_id == "alpilab_check.search_products":
            return ResultEnvelope(
                request_id="r",
                command_id="c",
                agent_id=agent_id,
                tool_id=tool_id,
                success=True,
                result={
                    "items": [
                        {
                            "id": "only-1",
                            "brand": "Apple",
                            "model": "iPhone 12",
                            "services": [{"name": "Batteria", "price": 40}],
                        }
                    ]
                },
                timestamp="2026-01-01T00:00:00+00:00",
            )
        return ResultEnvelope(
            request_id="g",
            command_id="g",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={
                "id": arguments["product_id"],
                "brand": "Apple",
                "model": "iPhone 12",
                "services": [{"name": "Batteria", "price": 40}],
            },
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    service = NaturalLanguageCommandService()
    await service.handle_user_message("repair-one", "d1", "Cerca iPhone 12 nel listino")
    session = rt.get_session("repair-one")
    assert session is not None
    msg = [m for m in session.messages if m.role == "assistant"][-1].content
    assert msg == "Ho trovato Apple iPhone 12. Cosa vuoi sapere?"
    assert "Batteria" not in msg
    assert calls == ["alpilab_check.search_products"]
    assert session.product_search_context is not None
    assert session.product_search_context.selected_product_id == "only-1"

    await service.handle_user_message("repair-one", "d1", "quanto costa la batteria?")
    assert calls[-1] == "alpilab_check.get_product"


@pytest.mark.asyncio
async def test_empty_search_then_mock_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation import natural_language_service as nls_mod
    from app.realtime import session_manager as sm_mod

    rt = RealtimeSessionManager()
    rt.create_session("repair-empty", seed_demo=False)
    _register_agent("repair-empty")
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    async def mock_execute(session_id, agent_id, tool_id, arguments=None, **kwargs):
        return ResultEnvelope(
            request_id="e",
            command_id="e",
            agent_id=agent_id,
            tool_id=tool_id,
            success=True,
            result={"items": []},
            timestamp="2026-01-01T00:00:00+00:00",
        )

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    service = NaturalLanguageCommandService()
    await service.handle_user_message("repair-empty", "d1", "Cerca Samsung nel listino")
    session = rt.get_session("repair-empty")
    assert session is not None
    assert session.product_search_context is None
    assert [m for m in session.messages if m.role == "assistant"][-1].content == (
        "Non ho trovato prodotti nel listino per questa ricerca."
    )
    await service.handle_user_message("repair-empty", "d1", "Quanto costa lo schermo?")
    assert any("[MOCK]" in m.content for m in session.messages if m.role == "assistant")


@pytest.mark.asyncio
async def test_followup_without_context_uses_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.conversation import natural_language_service as nls_mod
    from app.realtime import session_manager as sm_mod

    rt = RealtimeSessionManager()
    rt.create_session("no-ctx", seed_demo=False)
    monkeypatch.setattr(sm_mod, "realtime_manager", rt)

    async def mock_execute(*args, **kwargs):
        raise AssertionError("should not run")

    monkeypatch.setattr(nls_mod.tool_execution_service, "execute_tool", mock_execute)
    await NaturalLanguageCommandService().handle_user_message(
        "no-ctx", "d1", "Quanto costa lo schermo?"
    )
    session = rt.get_session("no-ctx")
    assert session is not None
    assert [m for m in session.messages if m.role == "assistant"][-1].content.startswith(
        "[MOCK]"
    )


@pytest.mark.parametrize(
    "text",
    [
        "Il mio iPhone non si accende",
        "Quanto costa riparare un iPhone?",
        "Ho un iPhone con lo schermo rotto",
    ],
)
def test_general_conversation_not_hijacked(text: str) -> None:
    assert resolve_product_followup(text, _s24_context()).outcome == FollowUpOutcome.NO_MATCH
    assert NaturalLanguageCommandParser().parse(text).outcome == ParseOutcome.CONVERSATION


def test_disambiguation_message_layout() -> None:
    msg = format_disambiguation_message(_s24_items())
    assert "Ho trovato 4 modelli:" in msg
    assert msg.strip().endswith("Quale intendi?")
