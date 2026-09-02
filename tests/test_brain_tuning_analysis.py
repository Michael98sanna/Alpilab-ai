"""Tests for Brain tuning analysis (synthetic in-memory data only)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai.brain_tuning_analysis import (
    MIN_RELIABLE_SAMPLE,
    AnalysisContext,
    ClassificationAnalysis,
    ClassificationRecord,
    SimilarityAnalysis,
    TuningReport,
    analyze_classification,
    analyze_similarity,
    classification_verdict,
    collect_classification_records,
    format_report,
    format_report_markdown,
    run_analysis,
    tokenize_for_keywords,
)
from app.ai.smart_knowledge_base import SmartKnowledgeBase
from app.knowledge.embeddings import HashEmbedder, LazySentenceTransformerEmbedder
from app.models.database import Base
from app.models.orm_models import (
    DiagnosisConfirmation,
    DiagnosticCard,
    DiagnosticMessage,
    KnowledgeEmbedding,
    RouteEvent,
)


class StubSemanticEmbedder(LazySentenceTransformerEmbedder):
    def encode(self, text: str):
        seed = abs(hash(text)) % 997
        vec = np.zeros(384, dtype=np.float64)
        vec[seed % 384] = 1.0
        vec[(seed + 7) % 384] = 0.5
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec


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


def _seed_card(db_session) -> str:
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


def test_classification_distribution_and_unknown_rate():
    records = [
        ClassificationRecord("display nero", "display", "message"),
        ClassificationRecord("batteria scarica", "battery", "message"),
        ClassificationRecord("non parte dopo caduta", "unknown", "message"),
        ClassificationRecord(None, "display", "route_event"),
    ]
    result = analyze_classification(records)
    by_type = {dtype: count for dtype, count, _ in result.distribution}
    assert by_type["display"] == 2
    assert by_type["battery"] == 1
    assert by_type["unknown"] == 1
    assert result.unknown_rate == pytest.approx(0.25)
    assert result.total_records == 4


@pytest.mark.parametrize(
    ("rate", "level"),
    [
        (0.05, "ok"),
        (0.15, "warn"),
        (0.40, "bad"),
    ],
)
def test_classification_verdict_thresholds(rate, level):
    _verdict, verdict_level = classification_verdict(rate)
    assert verdict_level == level


def test_tokenize_excludes_stopwords_and_min_length():
    tokens = tokenize_for_keywords("il telefono non si accende dopo un update ios")
    assert "telefono" in tokens
    assert "accende" in tokens
    assert "update" in tokens
    assert "il" not in tokens
    assert "non" not in tokens


def test_hash_mode_skips_similarity_section(db_session):
    kb = SmartKnowledgeBase(db_session, embedder=HashEmbedder())
    kb.index_case(
        text="display nero",
        diagnosis="flex",
        solution="swap",
        diagnosis_type="display",
        device_type="iphone",
    )
    cutoff = datetime.now(UTC) - timedelta(days=30)
    result = analyze_similarity(db_session, kb, cutoff)
    assert result.skipped is True
    assert "hash" in result.skip_reason.lower()


def test_sample_warning_when_less_than_20_cases(db_session):
    card_id = _seed_card(db_session)
    db_session.add(
        DiagnosticMessage(
            id=str(uuid.uuid4()),
            card_id=card_id,
            role="user",
            content="display nero",
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    report = run_analysis(db_session, days=30, use_color=False)
    assert report.context.total_cases < MIN_RELIABLE_SAMPLE
    assert report.sample_warning is True
    text = format_report(report, use_color=False)
    assert "campione inferiore a 20 casi" in text


def test_read_only_session_does_not_write(db_session):
    card_id = _seed_card(db_session)
    db_session.add(
        DiagnosisConfirmation(
            id=str(uuid.uuid4()),
            card_id=card_id,
            ai_diagnosis="schermo nero",
            feedback="confirmed",
            pre_feedback_confidence=0.8,
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    def fail_write(*args, **kwargs):
        raise AssertionError("Lo script non deve scrivere sul database")

    db_session.add = fail_write  # type: ignore[method-assign]
    db_session.commit = fail_write  # type: ignore[method-assign]
    db_session.delete = fail_write  # type: ignore[method-assign]

    report = run_analysis(db_session, days=30, use_color=False)
    text = format_report(report, use_color=False)
    assert "ALPILAB Brain" in text


def test_export_markdown_has_no_ansi():
    ctx = AnalysisContext(
        days=30,
        cutoff=datetime.now(UTC),
        embedder_kind="hash",
        maturity_stage="cold",
        total_cases=5,
        indexed_entries=1,
        use_color=False,
    )
    classification = ClassificationAnalysis(
        distribution=[("unknown", 3, 0.6), ("display", 2, 0.4)],
        unknown_rate=0.6,
        verdict="Problema serio",
        verdict_level="bad",
        unknown_samples=["non parte da solo"],
        keyword_suggestions=[("parte", 2, "nuova categoria?")],
        unused_categories=["water"],
        collision_pairs=[],
        total_records=5,
    )
    similarity = SimilarityAnalysis(
        skipped=True,
        skip_reason="Embedder in modalità hash",
    )
    tuning = TuningReport(
        context=ctx,
        classification=classification,
        similarity=similarity,
        summary_lines=["Campione piccolo"],
        sample_warning=True,
        section="all",
    )
    md = format_report_markdown(tuning)
    assert "\033[" not in md


def test_semantic_similarity_analysis_runs(db_session):
    embedder = StubSemanticEmbedder()
    kb = SmartKnowledgeBase(db_session, embedder=embedder)
    kb.index_case(
        text="display nero iphone",
        diagnosis="flex display",
        solution="sostituire",
        diagnosis_type="display",
        device_type="iphone",
        confidence=0.9,
    )
    kb.index_case(
        text="schermo nero dopo caduta",
        diagnosis="flex oled",
        solution="sostituire flex",
        diagnosis_type="display",
        device_type="iphone",
        confidence=0.88,
    )
    kb.index_case(
        text="batteria si scarica velocemente",
        diagnosis="bms",
        solution="cambio batteria",
        diagnosis_type="battery",
        device_type="iphone",
        confidence=0.9,
    )
    cutoff = datetime.now(UTC) - timedelta(days=30)
    result = analyze_similarity(db_session, kb, cutoff)
    assert result.skipped is False
    assert result.same_type_similarities
    assert result.threshold_table


def test_collect_records_from_db(db_session):
    card_id = _seed_card(db_session)
    now = datetime.now(UTC)
    db_session.add(
        DiagnosisConfirmation(
            id=str(uuid.uuid4()),
            card_id=card_id,
            ai_diagnosis="touch non risponde",
            feedback="confirmed",
            pre_feedback_confidence=0.7,
            created_at=now,
        )
    )
    db_session.add(
        RouteEvent(
            id=str(uuid.uuid4()),
            timestamp=now,
            diagnosis_type="display",
            kb_mode="semantic",
            strong_match=False,
            used_online=True,
            provider="gpt4",
            latency_ms=100,
        )
    )
    db_session.commit()

    records = collect_classification_records(db_session, now - timedelta(days=1))
    assert len(records) >= 2
    types = {record.diagnosis_type for record in records}
    assert "display" in types
