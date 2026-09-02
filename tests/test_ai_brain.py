"""Tests for ALPILAB Brain AI."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.learning_engine import LearningEngine
from app.ai.providers.base import LLMProvider
from app.ai.router import BrainRouter, _parse_validation_json
from app.ai.schemas import LLMResponse, KnowledgeCase, ResponseSource
from app.ai.smart_knowledge_base import SmartKnowledgeBase
from app.ai.task_classifier import TaskType, classify_task
from app.knowledge.embeddings import HashEmbedder, LazySentenceTransformerEmbedder
from app.main import app
from app.models.database import Base
from app.models.orm_models import DiagnosticCard, KnowledgeEmbedding, RouteEvent


class TrackingProvider(LLMProvider):
    name = "gpt4"
    model = "test-model"
    env_var = "TEST_KEY"
    calls = 0

    def __init__(self) -> None:
        super().__init__(enabled=True)
        self._api_key = "test"

    def complete(self, prompt, *, system_prompt=None, temperature=0.3, max_tokens=1024):
        TrackingProvider.calls += 1
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=f"AI answer for: {prompt[:40]}",
            confidence=0.8,
        )


class FailingProvider(LLMProvider):
    name = "claude"
    model = "fail-model"
    env_var = "TEST_KEY2"

    def __init__(self) -> None:
        super().__init__(enabled=True)
        self._api_key = "test"

    def complete(self, prompt, *, system_prompt=None, temperature=0.3, max_tokens=1024):
        raise RuntimeError("provider down")


class ValidationDisagreeProvider(LLMProvider):
    name = "gpt4"
    model = "test-model"
    env_var = "TEST_KEY"

    def __init__(self) -> None:
        super().__init__(enabled=True)
        self._api_key = "test"

    def complete(self, prompt, *, system_prompt=None, temperature=0.3, max_tokens=1024):
        if system_prompt and "JSON" in system_prompt:
            return LLMResponse(
                provider=self.name,
                model=self.model,
                content='{"agrees": false, "reason": "diagnosi errata", "alternative": "Risposta online corretta"}',
                confidence=0.85,
            )
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content="fallback online",
            confidence=0.8,
        )


class MalformedValidationProvider(LLMProvider):
    name = "gpt4"
    model = "test-model"
    env_var = "TEST_KEY"

    def __init__(self) -> None:
        super().__init__(enabled=True)
        self._api_key = "test"

    def complete(self, prompt, *, system_prompt=None, temperature=0.3, max_tokens=1024):
        if system_prompt and "JSON" in system_prompt:
            return LLMResponse(
                provider=self.name,
                model=self.model,
                content="Non sono d'accordo, verifica manualmente.",
                confidence=0.7,
            )
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content="unused",
            confidence=0.7,
        )


class SemanticStubEmbedder(LazySentenceTransformerEmbedder):
    def encode(self, text: str):
        import numpy as np

        return np.ones(384, dtype=np.float64) / (384**0.5)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def card(db_session):
    card_id = str(uuid.uuid4())
    db_session.add(
        DiagnosticCard(
            id=card_id,
            session_id="repair-test",
            device_id="iphone-13",
            device_name="iPhone 13",
        )
    )
    db_session.commit()
    return card_id


def test_smart_kb_search_finds_indexed_case(db_session):
    kb = SmartKnowledgeBase(db_session)
    kb.index_case(
        text="iPhone 12 non carica",
        diagnosis="Dock USB difettoso",
        solution="Sostituire connettore",
        diagnosis_type="charging",
        device_type="iphone-12",
        confidence=0.85,
    )
    results = kb.search_similar("problema ricarica iPhone 12", top_k=3)
    assert len(results) >= 1
    assert results[0].diagnosis == "Dock USB difettoso"


def test_cosine_similarity_identical_vectors():
    from app.ai.smart_knowledge_base import _cosine
    import numpy as np

    vec = np.array([1.0, 0.0, 0.0])
    assert abs(_cosine(vec, vec) - 1.0) < 0.001


def test_classify_all_task_types():
    assert classify_task("non si accende") == TaskType.DIAGNOSIS
    assert classify_task("cerca ricambio listino") == TaskType.KNOWLEDGE_SEARCH
    assert classify_task("spiega come funziona il PMIC") == TaskType.EXPLANATION
    assert classify_task("analizza panic log kernel") == TaskType.CODE_ANALYSIS
    assert classify_task("perché la scheda non risponde") == TaskType.REASONING
    assert classify_task("quanto costa") == TaskType.QUICK_ANSWER


def test_routing_empty_kb_calls_online_provider(db_session):
    TrackingProvider.calls = 0
    router = BrainRouter(db_session, providers=[TrackingProvider()])
    result = router.intelligent_route("display nero dopo caduta", device_type="iphone")
    assert TrackingProvider.calls == 1
    assert result.source == ResponseSource.ONLINE


def test_routing_strong_kb_skips_providers(db_session):
    TrackingProvider.calls = 0
    from app.knowledge.embeddings import LazySentenceTransformerEmbedder
    import numpy as np

    class SemanticStubEmbedder(LazySentenceTransformerEmbedder):
        def encode(self, text: str):
            return np.ones(384, dtype=np.float64) / (384**0.5)

    embedder = SemanticStubEmbedder()
    kb = SmartKnowledgeBase(db_session, embedder=embedder)
    entry = kb.index_case(
        text="iPhone 13 display nero dopo caduta",
        diagnosis="Flex display danneggiato",
        solution="Sostituire flex OLED",
        diagnosis_type="display",
        device_type="iphone-13",
        confidence=0.92,
    )
    entry.confirmation_count = 3
    db_session.commit()

    router = BrainRouter(db_session, providers=[], kb=kb)
    router.learning = LearningEngine(db_session, kb=kb)
    with patch.object(
        SmartKnowledgeBase,
        "search",
        return_value=[
            KnowledgeCase(
                id=entry.id,
                text=entry.text,
                diagnosis_type="display",
                device_type="iphone-13",
                diagnosis=entry.diagnosis,
                solution=entry.solution,
                confidence_score=0.92,
                confirmation_count=3,
                similarity=0.95,
            )
        ],
    ):
        result = router.intelligent_route(
            "display nero dopo caduta",
            device_type="iphone-13",
            diagnosis_type="display",
        )
    assert TrackingProvider.calls == 0
    assert result.source == ResponseSource.LOCAL_KB
    assert result.strong_match is True
    assert result.kb_mode == "semantic"


def test_fallback_chain_uses_second_provider(db_session):
    TrackingProvider.calls = 0
    router = BrainRouter(db_session, providers=[FailingProvider(), TrackingProvider()])
    result = router.route("test prompt")
    assert TrackingProvider.calls == 1
    assert result.provider == "gpt4"


def test_feedback_confirmed_success_boosts_confidence(db_session, card):
    kb = SmartKnowledgeBase(db_session)
    entry = kb.index_case(
        text="batteria si scarica velocemente",
        diagnosis="BMS difettoso",
        solution="Replace battery",
        diagnosis_type="battery",
        device_type="iphone",
        confidence=0.7,
        entry_id="kb-entry-1",
    )
    engine = LearningEngine(db_session)
    confirmation = engine.record_feedback(
        card_id=card,
        feedback="confirmed",
        provider="gpt4",
        pre_confidence=0.8,
        knowledge_entry_id=entry.id,
    )
    engine.record_outcome(
        confirmation.id,
        outcome="success",
        symptom_text="batteria si scarica velocemente",
        device_type="iphone",
        ai_diagnosis="BMS difettoso",
    )
    updated = db_session.get(KnowledgeEmbedding, entry.id)
    assert updated is not None
    assert updated.confidence_score > 0.7
    assert updated.confirmation_count >= 2


def test_feedback_corrected_indexes_correction_and_decays_wrong_entry(db_session, card):
    kb = SmartKnowledgeBase(db_session)
    wrong = kb.index_case(
        text="telefono surriscalda",
        diagnosis="CPU difettosa",
        solution="Reball CPU",
        diagnosis_type="thermal",
        device_type="iphone",
        confidence=0.75,
        entry_id="kb-wrong",
    )
    engine = LearningEngine(db_session)
    confirmation = engine.record_feedback(
        card_id=card,
        feedback="corrected",
        provider="claude",
        pre_confidence=0.7,
        knowledge_entry_id=wrong.id,
        correction_text="Flex batteria danneggiato causa surriscaldamento",
    )
    engine.record_outcome(
        confirmation.id,
        outcome="success",
        symptom_text="telefono surriscalda",
        device_type="iphone",
        ai_diagnosis="CPU difettosa",
    )
    updated_wrong = db_session.get(KnowledgeEmbedding, wrong.id)
    assert updated_wrong.confidence_score < 0.75
    new_entries = db_session.query(KnowledgeEmbedding).filter(
        KnowledgeEmbedding.id != wrong.id
    ).all()
    assert len(new_entries) >= 1
    assert "Flex batteria" in new_entries[0].diagnosis


def test_metrics_accuracy_by_type_and_provider(db_session, card):
    engine = LearningEngine(db_session)
    for _ in range(2):
        conf = engine.record_feedback(
            card_id=card,
            feedback="confirmed",
            provider="gpt4",
            pre_confidence=0.8,
        )
        engine.record_outcome(
            conf.id,
            outcome="success",
            symptom_text="display nero",
        )
    conf_fail = engine.record_feedback(
        card_id=card,
        feedback="rejected",
        provider="claude",
        pre_confidence=0.6,
    )
    engine.record_outcome(
        conf_fail.id,
        outcome="failed",
        symptom_text="display nero",
    )

    metrics = engine.get_accuracy("display")
    assert metrics["total"] == 3
    assert metrics["correct"] == 2
    assert abs(metrics["accuracy"] - 2 / 3) < 0.01

    provider_rows = engine.get_provider_metrics()
    gpt_row = next(row for row in provider_rows if row["provider"] == "gpt4")
    assert gpt_row["correct"] == 2
    assert gpt_row["total"] == 2


def _make_router(db_session, *, providers=None, embedder=None) -> BrainRouter:
    kb = SmartKnowledgeBase(db_session, embedder=embedder)
    router = BrainRouter(db_session, providers=providers or [], kb=kb)
    router.learning = LearningEngine(db_session, kb=kb)
    return router


def _strong_case(entry_id: str, entry: KnowledgeEmbedding) -> KnowledgeCase:
    return KnowledgeCase(
        id=entry_id,
        text=entry.text,
        diagnosis_type=entry.diagnosis_type,
        device_type=entry.device_type,
        diagnosis=entry.diagnosis,
        solution=entry.solution,
        confidence_score=entry.confidence_score,
        confirmation_count=entry.confirmation_count,
        similarity=0.95,
    )


def test_hash_mode_never_strong_match(db_session):
    TrackingProvider.calls = 0
    kb = SmartKnowledgeBase(db_session, embedder=HashEmbedder())
    entry = kb.index_case(
        text="iPhone 13 display nero",
        diagnosis="Flex display danneggiato",
        solution="Sostituire flex OLED",
        diagnosis_type="display",
        device_type="iphone-13",
        confidence=0.92,
    )
    router = _make_router(db_session, providers=[TrackingProvider()], embedder=HashEmbedder())
    with patch.object(
        SmartKnowledgeBase,
        "search",
        return_value=[_strong_case(entry.id, entry)],
    ):
        result = router.intelligent_route(
            "display nero dopo caduta",
            device_type="iphone-13",
            diagnosis_type="display",
        )
    assert result.strong_match is False
    assert result.kb_mode == "hash"
    assert result.source != ResponseSource.LOCAL_KB


def test_validation_disagree_overrides_and_penalizes(db_session):
    kb = SmartKnowledgeBase(db_session, embedder=SemanticStubEmbedder())
    entry = kb.index_case(
        text="display nero",
        diagnosis="Diagnosi locale sbagliata",
        solution="Soluzione locale",
        diagnosis_type="display",
        device_type="iphone-13",
        confidence=0.9,
    )
    router = _make_router(
        db_session, providers=[ValidationDisagreeProvider()], embedder=SemanticStubEmbedder()
    )
    with patch.object(
        SmartKnowledgeBase,
        "search",
        return_value=[_strong_case(entry.id, entry)],
    ):
        result = router.intelligent_route(
            "display nero",
            device_type="iphone-13",
            diagnosis_type="display",
        )
    updated = db_session.get(KnowledgeEmbedding, entry.id)
    assert result.validation.overridden is True
    assert result.source == ResponseSource.ONLINE
    assert "Risposta online corretta" in result.content
    assert updated is not None
    assert updated.confidence_score < 0.9


def test_disputed_entry_excluded_from_strong_match(db_session):
    kb = SmartKnowledgeBase(db_session, embedder=SemanticStubEmbedder())
    entry = kb.index_case(
        text="display nero",
        diagnosis="Vecchia diagnosi",
        solution="Vecchia soluzione",
        diagnosis_type="display",
        device_type="iphone-13",
        confidence=0.35,
    )
    entry.disputed = True
    db_session.commit()

    router = _make_router(db_session, providers=[TrackingProvider()], embedder=SemanticStubEmbedder())
    TrackingProvider.calls = 0
    result = router.intelligent_route(
        "display nero",
        device_type="iphone-13",
        diagnosis_type="display",
    )
    assert result.strong_match is False
    assert TrackingProvider.calls >= 1
    results = kb.search("display nero", diagnosis_type="display")
    assert all(item.id != entry.id for item in results)


def test_malformed_validation_json_keeps_local_case(db_session):
    kb = SmartKnowledgeBase(db_session, embedder=SemanticStubEmbedder())
    entry = kb.index_case(
        text="display nero",
        diagnosis="Diagnosi locale",
        solution="Soluzione locale",
        diagnosis_type="display",
        device_type="iphone-13",
        confidence=0.88,
    )
    router = _make_router(
        db_session,
        providers=[MalformedValidationProvider()],
        embedder=SemanticStubEmbedder(),
    )
    with patch.object(
        SmartKnowledgeBase,
        "search",
        return_value=[_strong_case(entry.id, entry)],
    ):
        result = router.intelligent_route(
            "display nero",
            device_type="iphone-13",
            diagnosis_type="display",
        )
    updated = db_session.get(KnowledgeEmbedding, entry.id)
    assert result.source == ResponseSource.LOCAL_KB
    assert result.validation.performed is False
    assert updated is not None
    assert updated.confidence_score == pytest.approx(0.88)


def test_penalize_marks_disputed_below_threshold(db_session):
    kb = SmartKnowledgeBase(db_session, embedder=HashEmbedder())
    entry = kb.index_case(
        text="test",
        diagnosis="d",
        solution="s",
        diagnosis_type="display",
        device_type="iphone",
        confidence=0.5,
    )
    before = kb.penalize_confidence(entry.id, amount=0.15)
    updated = db_session.get(KnowledgeEmbedding, entry.id)
    assert before == pytest.approx(0.5)
    assert updated is not None
    assert updated.confidence_score == pytest.approx(0.35)
    assert updated.disputed is True


@pytest.mark.parametrize(
    ("case_count", "strong_hits", "expected_stage"),
    [
        (5, 0, "cold"),
        (25, 0, "warming"),
        (60, 25, "mature"),
    ],
)
def test_kb_maturity_stages(db_session, case_count, strong_hits, expected_stage):
    kb = SmartKnowledgeBase(db_session, embedder=HashEmbedder())
    for index in range(case_count):
        kb.index_case(
            text=f"case {index}",
            diagnosis=f"diag {index}",
            solution="fix",
            diagnosis_type="display",
            device_type="iphone",
            confidence=0.9,
        )
    engine = LearningEngine(db_session, kb=kb)
    now = datetime.now(UTC)
    for _ in range(strong_hits):
        db_session.add(
            RouteEvent(
                id=str(uuid.uuid4()),
                timestamp=now - timedelta(days=1),
                diagnosis_type="display",
                kb_mode="semantic",
                strong_match=True,
                used_online=False,
                provider="local_kb",
                latency_ms=10,
            )
        )
    for _ in range(max(0, 30 - strong_hits)):
        db_session.add(
            RouteEvent(
                id=str(uuid.uuid4()),
                timestamp=now - timedelta(days=2),
                diagnosis_type="display",
                kb_mode="semantic",
                strong_match=False,
                used_online=True,
                provider="gpt4",
                latency_ms=100,
            )
        )
    db_session.commit()

    maturity = engine.get_kb_maturity()
    assert maturity["indexed_cases"] == case_count
    assert maturity["maturity_stage"] == expected_stage


def test_metrics_providers_route_returns_list(client):
    response = client.get("/api/v1/ai/metrics/providers")
    assert response.status_code == 200
    payload = response.json()
    assert "providers" in payload
    assert isinstance(payload["providers"], list)


def test_metrics_by_type_does_not_shadow_providers(client):
    response = client.get("/api/v1/ai/metrics/display")
    assert response.status_code == 200
    payload = response.json()
    assert payload["diagnosis_type"] == "display"
    assert "providers" not in payload


def test_brain_chat_without_cloud_providers(client, monkeypatch):
    for key in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "PERPLEXITY_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ALPILAB_OLLAMA_URL", "http://127.0.0.1:9")

    created = client.post(
        "/api/v1/diagnostic-cards",
        json={
            "session_id": "repair-test",
            "device_id": "iphone-13",
            "device_name": "iPhone 13",
        },
    )
    assert created.status_code == 200
    card_id = created.json()["id"]

    response = client.post(
        "/api/v1/ai/chat",
        json={"card_id": card_id, "message": "display nero dopo caduta"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["content"]
    assert payload["provider"] == "ollama"

