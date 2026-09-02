"""Read-only analysis helpers for Brain classification and similarity tuning."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.ai.learning_engine import LearningEngine, _DIAGNOSIS_KEYWORDS
from app.ai.smart_knowledge_base import LOCAL_KB_CONFIDENCE, STRONG_MATCH_THRESHOLD, SmartKnowledgeBase
from app.ai.smart_knowledge_base import _cosine
from app.models.orm_models import DiagnosisConfirmation, DiagnosticMessage, KnowledgeEmbedding, RouteEvent

SectionName = Literal["classification", "similarity", "summary", "all"]

STOPWORDS = frozenset(
    """
    a ad al alla alle allo ai agli all con da del della delle dello dei degli
    di e ed che chi come cosa cui dove dove quando dove per tra fra su sul sulla
    sotto sopra non ne ni il lo la i gli le un uno una un' un
    the and or of to in on at by for with from is are was were be been being
    this that these those it its he she they we you your my our their
    very just also only about into over after before than then very
    problema problem issue caso client cliente riparazione laboratorio
    """.split()
)

CLASSIFICATION_OK_MAX = 0.10
CLASSIFICATION_WARN_MAX = 0.25
MIN_RELIABLE_SAMPLE = 20
THRESHOLD_CANDIDATES = [round(x / 100, 2) for x in range(60, 96, 5)]
HISTOGRAM_BUCKET = 0.05


@dataclass
class ClassificationRecord:
    text: str | None
    diagnosis_type: str
    source: str


@dataclass
class AnalysisContext:
    days: int
    cutoff: datetime
    embedder_kind: str
    maturity_stage: str
    total_cases: int
    indexed_entries: int
    use_color: bool = True
    current_threshold: float = STRONG_MATCH_THRESHOLD


@dataclass
class ClassificationAnalysis:
    distribution: list[tuple[str, int, float]]
    unknown_rate: float
    verdict: str
    verdict_level: Literal["ok", "warn", "bad"]
    unknown_samples: list[str]
    keyword_suggestions: list[tuple[str, int, str]]
    unused_categories: list[str]
    collision_pairs: list[tuple[str, str, int]]
    total_records: int


@dataclass
class SimilarityAnalysis:
    skipped: bool
    skip_reason: str = ""
    same_type_similarities: list[float] = field(default_factory=list)
    diff_type_similarities: list[float] = field(default_factory=list)
    suggested_threshold: float = STRONG_MATCH_THRESHOLD
    threshold_table: list[dict[str, Any]] = field(default_factory=list)
    retroactive_impact: list[dict[str, Any]] = field(default_factory=list)
    problematic_entries: list[dict[str, Any]] = field(default_factory=list)
    orphan_entries: list[dict[str, Any]] = field(default_factory=list)
    criterion: str = ""


@dataclass
class TuningReport:
    context: AnalysisContext
    classification: ClassificationAnalysis
    similarity: SimilarityAnalysis
    summary_lines: list[str] = field(default_factory=list)
    sample_warning: bool = False
    section: SectionName = "all"


def match_all_categories(text: str) -> list[str]:
    normalized = text.lower()
    matched: list[str] = []
    for category, keywords in _DIAGNOSIS_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            matched.append(category)
    return matched


def classification_verdict(unknown_rate: float) -> tuple[str, Literal["ok", "warn", "bad"]]:
    pct = unknown_rate * 100
    if unknown_rate < CLASSIFICATION_OK_MAX:
        return f"OK — unknown al {pct:.1f}% (sotto il 10%)", "ok"
    if unknown_rate <= CLASSIFICATION_WARN_MAX:
        return f"Da rivedere — unknown al {pct:.1f}% (tra 10% e 25%)", "warn"
    return f"Problema serio — unknown al {pct:.1f}% (sopra il 25%)", "bad"


def tokenize_for_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[a-zàèéìòù0-9]{4,}", text.lower())
    return [token for token in tokens if token not in STOPWORDS]


def suggest_category_for_word(word: str) -> str:
    for category, keywords in _DIAGNOSIS_KEYWORDS.items():
        if any(word in keyword or keyword in word for keyword in keywords):
            return category
    return "nuova categoria?"


def _safe_query(default, fn):
    try:
        return fn()
    except (OperationalError, SQLAlchemyError):
        return default


def collect_classification_records(db: Session, cutoff: datetime) -> list[ClassificationRecord]:
    records: list[ClassificationRecord] = []

    confirmations = _safe_query(
        [],
        lambda: (
            db.query(DiagnosisConfirmation)
            .filter(DiagnosisConfirmation.created_at >= cutoff)
            .all()
        ),
    )
    for conf in confirmations:
        if conf.ai_diagnosis and conf.ai_diagnosis.strip():
            text = conf.ai_diagnosis.strip()
            records.append(
                ClassificationRecord(
                    text=text,
                    diagnosis_type=LearningEngine.extract_diagnosis_category(text),
                    source="confirmation",
                )
            )

    embeddings = _safe_query(
        [],
        lambda: (
            db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.created_at >= cutoff)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .all()
        ),
    )
    for entry in embeddings:
        text = entry.text.strip()
        if text:
            records.append(
                ClassificationRecord(
                    text=text,
                    diagnosis_type=LearningEngine.extract_diagnosis_category(text),
                    source="embedding",
                )
            )

    events = _safe_query(
        [],
        lambda: db.query(RouteEvent).filter(RouteEvent.timestamp >= cutoff).all(),
    )
    for event in events:
        records.append(
            ClassificationRecord(
                text=None,
                diagnosis_type=event.diagnosis_type or "unknown",
                source="route_event",
            )
        )

    messages = _safe_query(
        [],
        lambda: (
            db.query(DiagnosticMessage)
            .filter(DiagnosticMessage.created_at >= cutoff)
            .filter(DiagnosticMessage.role == "user")
            .all()
        ),
    )
    for msg in messages:
        text = msg.content.strip()
        if text:
            records.append(
                ClassificationRecord(
                    text=text,
                    diagnosis_type=LearningEngine.extract_diagnosis_category(text),
                    source="message",
                )
            )

    return records


def analyze_classification(records: list[ClassificationRecord]) -> ClassificationAnalysis:
    counts = Counter(record.diagnosis_type for record in records)
    total = sum(counts.values())
    distribution = [
        (dtype, count, (count / total if total else 0.0))
        for dtype, count in counts.most_common()
    ]
    distribution.sort(key=lambda item: (-item[1], item[0]))
    if any(item[0] == "unknown" for item in distribution):
        unknown_items = [item for item in distribution if item[0] == "unknown"]
        others = [item for item in distribution if item[0] != "unknown"]
        distribution = sorted(others, key=lambda item: -item[1]) + unknown_items

    unknown_count = counts.get("unknown", 0)
    unknown_rate = unknown_count / total if total else 0.0
    verdict, verdict_level = classification_verdict(unknown_rate)

    unknown_samples: list[str] = []
    for record in records:
        if record.diagnosis_type == "unknown" and record.text:
            snippet = record.text[:120]
            if snippet not in unknown_samples:
                unknown_samples.append(snippet)
        if len(unknown_samples) >= 15:
            break

    unknown_texts = [
        record.text for record in records if record.diagnosis_type == "unknown" and record.text
    ]
    word_counts = Counter()
    for text in unknown_texts:
        word_counts.update(tokenize_for_keywords(text))
    keyword_suggestions = [
        (word, count, suggest_category_for_word(word))
        for word, count in word_counts.most_common(20)
    ]

    used_categories = {dtype for dtype in counts if dtype != "unknown"}
    unused_categories = (
        sorted(set(_DIAGNOSIS_KEYWORDS) - used_categories) if total > 0 else []
    )

    collision_counter: Counter[tuple[str, str]] = Counter()
    for record in records:
        if not record.text:
            continue
        matched = match_all_categories(record.text)
        if len(matched) < 2:
            continue
        for i, left in enumerate(matched):
            for right in matched[i + 1 :]:
                pair = tuple(sorted((left, right)))
                collision_counter[pair] += 1
    collision_pairs = [
        (left, right, count) for (left, right), count in collision_counter.most_common(10)
    ]

    return ClassificationAnalysis(
        distribution=distribution,
        unknown_rate=unknown_rate,
        verdict=verdict,
        verdict_level=verdict_level,
        unknown_samples=unknown_samples,
        keyword_suggestions=keyword_suggestions,
        unused_categories=unused_categories,
        collision_pairs=collision_pairs,
        total_records=total,
    )


def _histogram(values: list[float], bucket: float = HISTOGRAM_BUCKET) -> list[tuple[str, int]]:
    if not values:
        return []
    max_val = 1.0
    bins: dict[str, int] = {}
    for value in values:
        idx = min(int(value / bucket), int(max_val / bucket) - 1)
        low = idx * bucket
        high = low + bucket
        label = f"{low:.2f}-{high:.2f}"
        bins[label] = bins.get(label, 0) + 1
    return sorted(bins.items(), key=lambda item: item[0])


def _pair_similarities(entries: list[KnowledgeEmbedding]) -> tuple[list[float], list[float]]:
    same: list[float] = []
    diff: list[float] = []
    for i, left in enumerate(entries):
        left_vec = np.asarray(left.embedding_json, dtype=np.float64)
        for right in entries[i + 1 :]:
            right_vec = np.asarray(right.embedding_json, dtype=np.float64)
            sim = _cosine(left_vec, right_vec)
            if left.diagnosis_type == right.diagnosis_type:
                same.append(sim)
            else:
                diff.append(sim)
    return same, diff


def suggest_similarity_threshold(
    same: list[float], diff: list[float]
) -> tuple[float, str]:
    criterion = (
        "Massimizza la precision sulle coppie stesso-tipo mantenendo recall >= 0.50 "
        "sulle coppie stesso-tipo."
    )
    if not same:
        return STRONG_MATCH_THRESHOLD, criterion

    best_threshold = STRONG_MATCH_THRESHOLD
    best_precision = -1.0
    for threshold in THRESHOLD_CANDIDATES:
        same_above = sum(1 for value in same if value >= threshold)
        diff_above = sum(1 for value in diff if value >= threshold)
        total_above = same_above + diff_above
        if total_above == 0:
            continue
        precision = same_above / total_above
        recall = same_above / len(same)
        if recall >= 0.50 and precision > best_precision:
            best_precision = precision
            best_threshold = threshold

    if best_precision < 0:
        best_threshold = STRONG_MATCH_THRESHOLD
    return best_threshold, criterion


def build_threshold_table(same: list[float], diff: list[float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for threshold in THRESHOLD_CANDIDATES:
        same_above = sum(1 for value in same if value >= threshold)
        diff_above = sum(1 for value in diff if value >= threshold)
        rows.append(
            {
                "threshold": threshold,
                "same_type_above": same_above,
                "diff_type_above": diff_above,
            }
        )
    return rows


def _best_match_for_text(
    text: str, entries: list[KnowledgeEmbedding], embedder: Any
) -> tuple[float, KnowledgeEmbedding | None]:
    if not entries:
        return 0.0, None
    query_vec = np.asarray(embedder.encode(text.strip()), dtype=np.float64)
    best_sim = -1.0
    best_entry: KnowledgeEmbedding | None = None
    for entry in entries:
        vec = np.asarray(entry.embedding_json, dtype=np.float64)
        sim = _cosine(query_vec, vec)
        if sim > best_sim:
            best_sim = sim
            best_entry = entry
    return best_sim, best_entry


def estimate_retroactive_impact(
    db: Session,
    cutoff: datetime,
    entries: list[KnowledgeEmbedding],
    embedder: Any,
    *,
    current_threshold: float = STRONG_MATCH_THRESHOLD,
) -> list[dict[str, Any]]:
    query_texts: list[str] = []
    messages = _safe_query(
        [],
        lambda: (
            db.query(DiagnosticMessage)
            .filter(DiagnosticMessage.created_at >= cutoff)
            .filter(DiagnosticMessage.role == "user")
            .all()
        ),
    )
    query_texts.extend(msg.content.strip() for msg in messages if msg.content.strip())

    events = _safe_query(
        [],
        lambda: db.query(RouteEvent).filter(RouteEvent.timestamp >= cutoff).all(),
    )
    baseline_strong = sum(1 for event in events if event.strong_match)

    matches: list[tuple[float, float]] = []
    for text in query_texts:
        sim, entry = _best_match_for_text(text, entries, embedder)
        if entry is None:
            continue
        matches.append((sim, entry.confidence_score))

    rows: list[dict[str, Any]] = []
    for threshold in THRESHOLD_CANDIDATES:
        projected = sum(
            1
            for sim, confidence in matches
            if sim >= threshold and confidence >= LOCAL_KB_CONFIDENCE
        )
        current_projected = sum(
            1
            for sim, confidence in matches
            if sim >= current_threshold and confidence >= LOCAL_KB_CONFIDENCE
        )
        rows.append(
            {
                "threshold": threshold,
                "projected_strong_matches": projected,
                "delta_vs_current": projected - current_projected,
                "baseline_logged_strong": baseline_strong,
            }
        )
    return rows


def find_problematic_entries(
    entries: list[KnowledgeEmbedding], threshold: float, *, limit: int = 10
) -> list[dict[str, Any]]:
    problematic: list[dict[str, Any]] = []
    for entry in entries:
        vec = np.asarray(entry.embedding_json, dtype=np.float64)
        best_sim = 0.0
        best_other: KnowledgeEmbedding | None = None
        for other in entries:
            if other.id == entry.id:
                continue
            if other.diagnosis_type == entry.diagnosis_type:
                continue
            sim = _cosine(vec, np.asarray(other.embedding_json, dtype=np.float64))
            if sim > best_sim:
                best_sim = sim
                best_other = other
        if best_sim > threshold and best_other is not None:
            problematic.append(
                {
                    "entry_id": entry.id,
                    "entry_type": entry.diagnosis_type,
                    "other_type": best_other.diagnosis_type,
                    "similarity": best_sim,
                    "text": entry.text[:80],
                }
            )
    problematic.sort(key=lambda item: item["similarity"], reverse=True)
    return problematic[:limit]


def find_orphan_entries(
    entries: list[KnowledgeEmbedding], *, min_neighbor: float = 0.5
) -> list[dict[str, Any]]:
    orphans: list[dict[str, Any]] = []
    for entry in entries:
        vec = np.asarray(entry.embedding_json, dtype=np.float64)
        best = 0.0
        for other in entries:
            if other.id == entry.id:
                continue
            sim = _cosine(vec, np.asarray(other.embedding_json, dtype=np.float64))
            best = max(best, sim)
        if best < min_neighbor:
            orphans.append(
                {
                    "entry_id": entry.id,
                    "diagnosis_type": entry.diagnosis_type,
                    "best_similarity": best,
                    "text": entry.text[:80],
                }
            )
    orphans.sort(key=lambda item: item["best_similarity"])
    return orphans


def analyze_similarity(
    db: Session,
    kb: SmartKnowledgeBase,
    cutoff: datetime,
    *,
    current_threshold: float = STRONG_MATCH_THRESHOLD,
) -> SimilarityAnalysis:
    if not kb.is_semantic:
        return SimilarityAnalysis(
            skipped=True,
            skip_reason=(
                "Embedder in modalità hash — la sezione similarity è priva di significato. "
                "Installa sentence-transformers per abilitare l'analisi semantica."
            ),
        )

    entries = _safe_query(
        [],
        lambda: (
            db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .filter(KnowledgeEmbedding.disputed.is_(False))
            .all()
        ),
    )
    if len(entries) < 2:
        return SimilarityAnalysis(
            skipped=True,
            skip_reason="Meno di 2 entry indicizzate: impossibile calcolare similarity interne.",
        )

    same, diff = _pair_similarities(entries)
    suggested, criterion = suggest_similarity_threshold(same, diff)
    table = build_threshold_table(same, diff)
    retro = estimate_retroactive_impact(
        db, cutoff, entries, kb.embedder, current_threshold=current_threshold
    )
    problematic = find_problematic_entries(entries, current_threshold)
    orphans = find_orphan_entries(entries)

    return SimilarityAnalysis(
        skipped=False,
        same_type_similarities=same,
        diff_type_similarities=diff,
        suggested_threshold=suggested,
        threshold_table=table,
        retroactive_impact=retro,
        problematic_entries=problematic,
        orphan_entries=orphans,
        criterion=criterion,
    )


def build_summary(
    ctx: AnalysisContext,
    classification: ClassificationAnalysis,
    similarity: SimilarityAnalysis,
) -> list[str]:
    lines: list[str] = []

    if classification.verdict_level == "bad" and classification.keyword_suggestions:
        top_words = ", ".join(word for word, _, _ in classification.keyword_suggestions[:3])
        suggestions = classification.keyword_suggestions[:3]
        targets = []
        for word, _, category in suggestions:
            if category == "nuova categoria?":
                targets.append(f'valutare keyword "{word}" in una categoria nuova')
            else:
                targets.append(f'aggiungere "{word}" a `{category}`')
        lines.append(
            f"Priorità classificazione: unknown elevato ({classification.unknown_rate:.0%}). "
            f"Parole ricorrenti: {top_words}. Azione: {', '.join(targets)}."
        )
    elif classification.verdict_level == "warn":
        lines.append(
            "Rivedi le keyword in `learning_engine.py`: unknown supera il 10%. "
            "Usa i campioni non classificati per ampliare il dizionario."
        )
    elif classification.unused_categories and classification.total_records > 0:
        lines.append(
            f"Categorie mai usate nel periodo ({', '.join(classification.unused_categories)}): "
            "verifica se le keyword sono obsolete o se non sono arrivate casistiche."
        )

    if classification.collision_pairs:
        left, right, count = classification.collision_pairs[0]
        lines.append(
            f"Collisione frequente `{left}`/`{right}` ({count} casi): "
            "ordina le keyword o rendi mutualmente esclusive le regole."
        )

    if not similarity.skipped:
        if similarity.suggested_threshold > ctx.current_threshold + 0.01:
            lines.append(
                f"Alza STRONG_MATCH_THRESHOLD da {ctx.current_threshold:.2f} a "
                f"{similarity.suggested_threshold:.2f}: riduce falsi positivi cross-tipo."
            )
        elif similarity.suggested_threshold < ctx.current_threshold - 0.01:
            lines.append(
                f"Abbassa STRONG_MATCH_THRESHOLD da {ctx.current_threshold:.2f} a "
                f"{similarity.suggested_threshold:.2f}: recupera match forti persi."
            )
        else:
            lines.append(
                f"Soglia attuale {ctx.current_threshold:.2f} coerente con la separazione osservata."
            )
        if similarity.problematic_entries:
            lines.append(
                f"Controlla {len(similarity.problematic_entries)} entry con alta similarity "
                "verso tipi diversi: possibili falsi positivi da rivalutare o escludere."
            )
        if similarity.orphan_entries:
            lines.append(
                f"{len(similarity.orphan_entries)} entry orfane (nessun vicino > 0.5): "
                "riformula testo/diagnosi o accetta casistiche uniche."
            )

    if ctx.total_cases < MIN_RELIABLE_SAMPLE:
        lines.append(
            "Campione ancora piccolo: ripeti l'analisi dopo almeno 20 casi reali prima di cambiare soglie."
        )

    if not lines:
        lines.append(
            "Nessuna azione urgente: classificazione e similarity sembrano allineate al campione attuale."
        )

    return lines[:8]


def build_context(db: Session, days: int, *, use_color: bool = True) -> AnalysisContext:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    kb = SmartKnowledgeBase(db)
    engine = LearningEngine(db, kb=kb)
    maturity = _safe_query(
        {
            "maturity_stage": "cold",
            "indexed_cases": 0,
        },
        engine.get_kb_maturity,
    )
    records = collect_classification_records(db, cutoff)
    indexed = _safe_query(
        0,
        lambda: (
            db.query(KnowledgeEmbedding)
            .filter(KnowledgeEmbedding.excluded.is_(False))
            .filter(KnowledgeEmbedding.disputed.is_(False))
            .count()
        ),
    )
    return AnalysisContext(
        days=days,
        cutoff=cutoff,
        embedder_kind=kb.embedder_kind,
        maturity_stage=maturity["maturity_stage"],
        total_cases=len(records),
        indexed_entries=indexed,
        use_color=use_color,
    )


def run_analysis(
    db: Session,
    *,
    days: int = 30,
    section: SectionName = "all",
    use_color: bool = True,
) -> TuningReport:
    ctx = build_context(db, days, use_color=use_color)
    records = collect_classification_records(db, ctx.cutoff)
    classification = analyze_classification(records)
    kb = SmartKnowledgeBase(db)
    similarity = analyze_similarity(db, kb, ctx.cutoff, current_threshold=ctx.current_threshold)
    summary_lines = build_summary(ctx, classification, similarity)

    if section == "classification":
        similarity = SimilarityAnalysis(skipped=True, skip_reason="Sezione non richiesta.")
        summary_lines = []
    elif section == "similarity":
        classification = ClassificationAnalysis(
            distribution=[],
            unknown_rate=0.0,
            verdict="",
            verdict_level="ok",
            unknown_samples=[],
            keyword_suggestions=[],
            unused_categories=[],
            collision_pairs=[],
            total_records=0,
        )
        summary_lines = []
    elif section == "summary":
        pass

    sample_warning = ctx.total_cases < MIN_RELIABLE_SAMPLE
    return TuningReport(
        context=ctx,
        classification=classification,
        similarity=similarity,
        summary_lines=summary_lines if section in {"all", "summary"} else [],
        sample_warning=sample_warning,
        section=section,
    )


def _supports_color(use_color: bool) -> bool:
    if not use_color:
        return False
    try:
        import sys

        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    except Exception:
        return False


def _colorize(text: str, code: str, *, enabled: bool) -> str:
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _verdict_color(level: str) -> str:
    return {"ok": "32", "warn": "33", "bad": "31"}.get(level, "0")


def _ascii_bar(count: int, max_count: int, width: int = 30) -> str:
    if max_count <= 0:
        return ""
    filled = max(1, int(round(count / max_count * width))) if count else 0
    return "█" * filled


def render_histogram(values: list[float], title: str) -> list[str]:
    lines = [title]
    buckets = _histogram(values)
    if not buckets:
        lines.append("  (nessun dato)")
        return lines
    max_count = max(count for _, count in buckets)
    for label, count in buckets:
        lines.append(f"  {label} | {_ascii_bar(count, max_count)} {count}")
    return lines


def format_report(report: TuningReport, *, use_color: bool | None = None) -> str:
    enabled = _supports_color(report.context.use_color if use_color is None else use_color)
    ctx = report.context
    lines: list[str] = []

    lines.append("=" * 72)
    lines.append("ALPILAB Brain — Analisi taratura")
    lines.append("=" * 72)
    lines.append(
        f"Finestra: ultimi {ctx.days} giorni (da {ctx.cutoff.date().isoformat()}) | "
        f"Casi analizzati: {ctx.total_cases} | Entry KB: {ctx.indexed_entries} | "
        f"Embedder: {ctx.embedder_kind} | Maturità: {ctx.maturity_stage}"
    )
    if report.sample_warning:
        warning = (
            "ATTENZIONE: campione inferiore a 20 casi — le conclusioni sono indicative, "
            "non affidabili per tarare in produzione."
        )
        lines.append(_colorize(warning, "33", enabled=enabled))

    show_classification = report.section in {"all", "classification"}
    show_similarity = report.section in {"all", "similarity"}
    show_summary = report.section in {"all", "summary"}

    if show_classification:
        lines.append("")
        lines.append("SEZIONE 1 — Qualità classificazione")
        lines.append("-" * 72)
        if not report.classification.distribution:
            lines.append("Nessun dato di classificazione nel periodo selezionato.")
            lines.append("")
            lines.append(
                _colorize(
                    "Verdetto: n/d — nessun campione nel periodo",
                    "33",
                    enabled=enabled,
                )
            )
        else:
            lines.append(f"{'Tipo':<16} {'Conteggio':>10} {'Percentuale':>12}")
            for dtype, count, pct in report.classification.distribution:
                label = dtype
                if dtype == "unknown":
                    label = _colorize(dtype, "31", enabled=enabled)
                lines.append(f"{label:<16} {count:>10} {pct * 100:>11.1f}%")

            verdict = report.classification.verdict
            lines.append("")
            lines.append(
                _colorize(
                    f"Verdetto: {verdict}",
                    _verdict_color(report.classification.verdict_level),
                    enabled=enabled,
                )
            )

            if report.classification.unknown_samples:
                lines.append("")
                lines.append("Campioni non classificati (unknown):")
                for sample in report.classification.unknown_samples:
                    lines.append(f"  • {sample}")

            if report.classification.keyword_suggestions:
                lines.append("")
                lines.append("Suggerimenti keyword (da testi unknown):")
                lines.append(f"{'Parola':<22} {'Freq':>6}  Suggerimento")
                for word, count, suggestion in report.classification.keyword_suggestions:
                    lines.append(f"{word:<22} {count:>6}  → {suggestion}")

            if report.classification.unused_categories:
                lines.append("")
                lines.append(
                    "Categorie mai usate: "
                    + ", ".join(report.classification.unused_categories)
                )

            if report.classification.collision_pairs:
                lines.append("")
                lines.append("Collisioni (keyword multi-categoria):")
                for left, right, count in report.classification.collision_pairs:
                    lines.append(f"  • {left} + {right}: {count} occorrenze")

    if show_similarity and not report.similarity.skipped:
        sim = report.similarity
        lines.append("")
        lines.append("SEZIONE 2 — Taratura soglia similarity")
        lines.append("-" * 72)
        lines.append(f"Soglia attuale: {ctx.current_threshold:.2f}")
        lines.append(f"Criterio suggerimento: {sim.criterion}")
        lines.append(f"Soglia suggerita: {sim.suggested_threshold:.2f}")
        lines.append("")
        lines.extend(render_histogram(sim.same_type_similarities, "Distribuzione coppie STESSO tipo:"))
        lines.append("")
        lines.extend(render_histogram(sim.diff_type_similarities, "Distribuzione coppie TIPO DIVERSO:"))
        lines.append("")
        lines.append(f"{'Soglia':>7} {'Stesso tipo':>12} {'Tipo diverso':>14}")
        for row in sim.threshold_table:
            lines.append(
                f"{row['threshold']:>7.2f} {row['same_type_above']:>12} {row['diff_type_above']:>14}"
            )
        if sim.retroactive_impact:
            lines.append("")
            lines.append("Impatto retroattivo (messaggi utente nel periodo):")
            lines.append(
                f"{'Soglia':>7} {'Match forti':>12} {'Δ vs 0.80':>10} "
                f"{'Log strong':>12}"
            )
            for row in sim.retroactive_impact:
                lines.append(
                    f"{row['threshold']:>7.2f} {row['projected_strong_matches']:>12} "
                    f"{row['delta_vs_current']:>+10} {row['baseline_logged_strong']:>12}"
                )
        if sim.problematic_entries:
            lines.append("")
            lines.append("Entry problematiche (alta similarity verso tipo diverso):")
            for item in sim.problematic_entries:
                lines.append(
                    f"  • {item['entry_id'][:8]}… [{item['entry_type']}→{item['other_type']}] "
                    f"sim={item['similarity']:.2f} — {item['text']}"
                )
        if sim.orphan_entries:
            lines.append("")
            lines.append("Entry orfane (nessun vicino > 0.5):")
            for item in sim.orphan_entries[:10]:
                lines.append(
                    f"  • {item['entry_id'][:8]}… [{item['diagnosis_type']}] "
                    f"best={item['best_similarity']:.2f} — {item['text']}"
                )
    elif show_similarity and report.similarity.skip_reason and report.similarity.skipped:
        if report.similarity.skip_reason != "Sezione non richiesta.":
            lines.append("")
            lines.append("SEZIONE 2 — Taratura soglia similarity")
            lines.append("-" * 72)
            lines.append(report.similarity.skip_reason)

    if show_summary and report.summary_lines:
        lines.append("")
        lines.append("SEZIONE 3 — Sintesi operativa")
        lines.append("-" * 72)
        for line in report.summary_lines:
            lines.append(f"• {line}")

    lines.append("")
    lines.append("=" * 72)
    return "\n".join(lines)


def format_report_markdown(report: TuningReport) -> str:
    plain = format_report(report, use_color=False)
    return plain.replace("█", "#")
