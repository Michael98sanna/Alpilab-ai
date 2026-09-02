"""Multi-LLM Brain router with knowledge-first routing."""



from __future__ import annotations



import hashlib

import json

import logging

import re

import time

from typing import Any, Literal



from sqlalchemy.orm import Session



from app.ai.learning_engine import LearningEngine

from app.ai.providers.base import LLMProvider

from app.ai.providers.registry import load_providers

from app.ai.schemas import (

    IntelligentRouteResult,

    KnowledgeCase,

    LLMResponse,

    ResponseSource,

    TaskType,

    ValidationInfo,

)

from app.ai.smart_knowledge_base import SmartKnowledgeBase, WEAK_MATCH_SIMILARITY

from app.ai.task_classifier import classify_task
from app.models.orm_models import KnowledgeEmbedding

logger = logging.getLogger(__name__)



_VALIDATION_SYSTEM = (

    "Sei un revisore tecnico ALPILAB. Rispondi SOLO con JSON valido, senza testo extra: "

    '{"agrees": true|false, "reason": "...", "alternative": "..."}'

)



_SYSTEM_PROMPTS: dict[TaskType, str] = {

    TaskType.DIAGNOSIS: (

        "Sei un tecnico senior di riparazione smartphone in laboratorio ALPILAB. "

        "Rispondi in italiano, in modo conciso e operativo. Proponi test concreti "

        "prima di concludere. Se non sei sicuro, dillo esplicitamente."

    ),

    TaskType.KNOWLEDGE_SEARCH: (

        "Sei un assistente tecnico ALPILAB. Fornisci informazioni su ricambi, "

        "schemi e procedure basandoti sul contesto fornito."

    ),

    TaskType.CODE_ANALYSIS: (

        "Sei un esperto di log iPhone/Android e panic log. Analizza errori in modo "

        "strutturato e suggerisci passi diagnostici concreti."

    ),

    TaskType.REASONING: (

        "Sei un tecnico ALPILAB. Ragiona passo passo sulle cause probabili "

        "senza inventare dati non verificati."

    ),

    TaskType.EXPLANATION: (

        "Spiega in modo chiaro e breve per un tecnico di laboratorio."

    ),

    TaskType.QUICK_ANSWER: (

        "Rispondi in modo breve e diretto per un tecnico di riparazione."

    ),

}



_DIAGNOSIS_SYNTHESIS_HINT = (
    "\n\nNota per il revisore: un modello locale gratuito (meno affidabile) ha già "
    "proposto questa ipotesi diagnostica per lo stesso caso. Verificala, correggila "
    "se necessario e arricchiscila con la tua competenza per dare una risposta "
    "finale unica, più completa e operativa. Se sei in disaccordo, spiega perché.\n"
    "Ipotesi locale:\n"
)

_MIN_USEFUL_LOCAL_ANSWER_CHARS = 30

# Cap Ollama's local draft length in the diagnosis combo: it only needs to be
# long enough for the cloud verifier to react to, not a finished answer.
_LOCAL_DRAFT_MAX_TOKENS = 350

_LOCAL_ANSWER_FALLBACK_MARKERS = (
    "nessun provider ai disponibile",
    "non disponibile",
)


_INTENT_PROVIDER_ORDER: dict[TaskType, tuple[str, ...]] = {

    TaskType.DIAGNOSIS: ("claude", "gpt4", "groq", "ollama"),

    TaskType.REASONING: ("claude", "gpt4", "groq", "ollama"),

    TaskType.CODE_ANALYSIS: ("claude", "gpt4", "groq", "ollama"),

    TaskType.KNOWLEDGE_SEARCH: ("perplexity", "gpt4", "groq", "ollama"),

    TaskType.QUICK_ANSWER: ("gpt4", "groq", "gemini", "ollama"),

    TaskType.EXPLANATION: ("gpt4", "groq", "gemini", "ollama"),

}

# Cloud providers tried (in order) to verify/enrich a local Ollama diagnosis.
# Gemini's free tier has a very low daily request cap, so Groq (much higher
# free limits) is tried first when both are configured.
_DIAGNOSIS_VERIFIER_ORDER: tuple[str, ...] = ("groq", "gemini")





def _parse_validation_json(content: str) -> dict[str, Any] | None:

    text = content.strip()

    try:

        parsed = json.loads(text)

        if isinstance(parsed, dict):

            return parsed

    except json.JSONDecodeError:

        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:

        return None

    try:

        parsed = json.loads(match.group())

        return parsed if isinstance(parsed, dict) else None

    except json.JSONDecodeError:

        return None





class BrainRouter:

    """Knowledge-first multi-LLM router."""



    def __init__(

        self,

        db: Session,

        *,

        providers: list[LLMProvider] | None = None,

        kb: SmartKnowledgeBase | None = None,

    ) -> None:

        self.db = db

        self.providers = providers if providers is not None else load_providers()

        self.kb = kb or SmartKnowledgeBase(db)

        self.learning = LearningEngine(db, kb=self.kb)

        self._cache: dict[str, IntelligentRouteResult] = {}



    def route(

        self,

        prompt: str,

        *,

        system_prompt: str | None = None,

        task_type: TaskType | None = None,

    ) -> IntelligentRouteResult:

        """Simple fallback chain without KB decision."""

        task = task_type or classify_task(prompt)

        system = system_prompt or _SYSTEM_PROMPTS[task]

        ordered = self._ordered_providers(task)

        for provider in ordered:

            try:

                llm = provider.complete(prompt, system_prompt=system)

                return IntelligentRouteResult(

                    content=llm.content,

                    source=ResponseSource.ONLINE,

                    provider=llm.provider,

                    model=llm.model,

                    confidence=llm.confidence,

                    task_type=task,

                    similar_cases=[],

                    latency_ms=llm.latency_ms,

                    tokens_used=llm.tokens_used,

                    kb_mode=self._resolve_kb_mode(),

                    used_online=True,

                )

            except Exception:

                logger.warning("Provider %s failed, trying next", provider.name, exc_info=True)

                continue

        return IntelligentRouteResult(

            content=(

                "Nessun provider AI disponibile. Configura le API key o avvia Ollama "

                "in locale."

            ),

            source=ResponseSource.ONLINE,

            provider="none",

            model="none",

            confidence=0.0,

            task_type=task,

            similar_cases=[],

            latency_ms=0,

            kb_mode=self._resolve_kb_mode(),

        )



    def intelligent_route(

        self,

        prompt: str,

        *,

        device_type: str = "unknown",

        symptom: str | None = None,

        diagnosis_type: str | None = None,

    ) -> IntelligentRouteResult:

        """Full pipeline: classify → KB search → route decision → LLM."""

        start = time.perf_counter()

        search_text = symptom or prompt

        # Classify on the raw symptom/message, not the context-enriched prompt:
        # the enriched prompt always contains template words like "sintomo"
        # ("Sintomo attuale: ..."), which would otherwise force every message
        # into TaskType.DIAGNOSIS and starve other providers (e.g. Gemini).
        task = classify_task(search_text)

        dtype = diagnosis_type or self.learning.extract_diagnosis_category(search_text)

        kb_mode = self._resolve_kb_mode()

        similar = self.kb.search(

            search_text,

            diagnosis_type=dtype if dtype != "unknown" else None,

            device_type=device_type,

            limit=5,

        )



        cache_key = self._cache_key(prompt, task, similar)

        cached = self._cache.get(cache_key)

        if cached is not None:

            return cached



        if self.kb.is_semantic:

            local_match = self.kb.best_local_match(similar)

            if local_match is not None:

                result = self._from_local_kb(

                    local_match, task, similar, prompt, start, dtype, kb_mode

                )

                result = self._finalize_route(result, dtype)

                self._cache[cache_key] = result

                return result



        if similar and max(c.similarity for c in similar) >= WEAK_MATCH_SIMILARITY:

            result = self._hybrid_route(prompt, task, similar, dtype, device_type, start, kb_mode)

        else:

            result = self._online_route(prompt, task, start, kb_mode)



        result = self._adjust_confidence(result, dtype)

        result = self._finalize_route(result, dtype)

        self._cache[cache_key] = result

        return result



    def _resolve_kb_mode(self) -> Literal["semantic", "hash", "disabled"]:

        if self.kb.indexed_case_count() == 0:

            return "disabled"

        return self.kb.embedder_kind



    def _from_local_kb(

        self,

        match: KnowledgeCase,

        task: TaskType,

        similar: list[KnowledgeCase],

        prompt: str,

        start: float,

        diagnosis_type: str,

        kb_mode: Literal["semantic", "hash", "disabled"],

    ) -> IntelligentRouteResult:

        local_content = (

            f"Dalla nostra esperienza su casi simili ({match.device_type}):\n\n"

            f"**Diagnosi:** {match.diagnosis}\n"

            f"**Soluzione:** {match.solution}\n\n"

            f"Confidenza interna: {match.confidence_score:.0%} "

            f"({match.confirmation_count} conferme)."

        )

        validation = ValidationInfo()

        used_online = False

        content = local_content

        provider = "local_kb"

        model = "knowledge_embeddings"

        confidence = match.confidence_score



        try:

            llm_validation = self._call_chain(

                (

                    f"Valida questa diagnosi locale per il caso: {prompt[:500]}\n"

                    f"Diagnosi proposta: {match.diagnosis}\n"

                    f"Soluzione proposta: {match.solution}"

                ),

                _VALIDATION_SYSTEM,

                task,

            )

            used_online = True

            parsed = _parse_validation_json(llm_validation.content)

            if parsed is None or "agrees" not in parsed:

                logger.debug("Validation JSON invalid or missing agrees field")

            else:

                validation.performed = True

                agrees = bool(parsed.get("agrees"))

                validation.agreed = agrees

                reason = str(parsed.get("reason") or "").strip()

                alternative = str(parsed.get("alternative") or "").strip()



                if agrees:

                    self.kb.boost_confidence(match.id, amount=0.02)

                    logger.info(

                        "KB validation agreed for entry %s (confidence boosted)",

                        match.id,

                    )

                else:

                    validation.overridden = True

                    before = self.kb.penalize_confidence(match.id, amount=0.15)

                    entry = self.db.get(KnowledgeEmbedding, match.id)

                    after = entry.confidence_score if entry else None

                    logger.info(

                        "KB validation disagreed for entry %s: confidence %.2f→%.2f — %s",

                        match.id,

                        before or 0.0,

                        after or 0.0,

                        reason or "no reason",

                    )

                    if alternative:

                        content = alternative

                        provider = llm_validation.provider

                        model = llm_validation.model

                        confidence = llm_validation.confidence

                    else:

                        llm_answer = self._route_completion(

                            prompt, _SYSTEM_PROMPTS[task], task

                        )

                        content = llm_answer.content

                        provider = llm_answer.provider

                        model = llm_answer.model

                        confidence = llm_answer.confidence



                    latency = int((time.perf_counter() - start) * 1000)

                    return IntelligentRouteResult(

                        content=content,

                        source=ResponseSource.ONLINE,

                        provider=provider,

                        model=model,

                        confidence=confidence,

                        task_type=task,

                        similar_cases=similar,

                        latency_ms=latency,

                        used_online=True,

                        kb_hits=len(similar),

                        strong_match=False,

                        kb_mode=kb_mode,

                        validation=validation,

                        metadata={"knowledge_entry_id": match.id, "diagnosis_type": diagnosis_type},

                    )

        except Exception:

            logger.debug("Local KB validation skipped (no online provider)", exc_info=True)



        latency = int((time.perf_counter() - start) * 1000)

        return IntelligentRouteResult(

            content=content,

            source=ResponseSource.LOCAL_KB,

            provider=provider if not used_online else llm_validation.provider,

            model=model if not used_online else llm_validation.model,

            confidence=confidence,

            task_type=task,

            similar_cases=similar,

            latency_ms=latency,

            used_online=used_online,

            kb_hits=len(similar),

            strong_match=True,

            kb_mode=kb_mode,

            validation=validation,

            metadata={"knowledge_entry_id": match.id, "diagnosis_type": diagnosis_type},

        )



    def _hybrid_route(

        self,

        prompt: str,

        task: TaskType,

        similar: list[KnowledgeCase],

        diagnosis_type: str,

        device_type: str,

        start: float,

        kb_mode: Literal["semantic", "hash", "disabled"],

    ) -> IntelligentRouteResult:

        context_lines = ["Casi simili già visti in laboratorio (solo contesto, non autoritativi):"]

        for index, case in enumerate(similar[:3], 1):

            context_lines.append(

                f"{index}. [{case.diagnosis_type}/{case.device_type}] "

                f"{case.text} → {case.diagnosis} (sol: {case.solution}, "

                f"sim={case.similarity:.0%})"

            )

        enriched = (

            "\n".join(context_lines)

            + f"\n\nDevice: {device_type}\nDomanda tecnico: {prompt}"

        )

        system = _SYSTEM_PROMPTS[task]

        llm = self._route_completion(enriched, system, task)

        latency = int((time.perf_counter() - start) * 1000)

        return IntelligentRouteResult(

            content=llm.content,

            source=ResponseSource.HYBRID,

            provider=llm.provider,

            model=llm.model,

            confidence=llm.confidence,

            task_type=task,

            similar_cases=similar,

            latency_ms=latency,

            tokens_used=llm.tokens_used,

            used_online=True,

            kb_hits=len(similar),

            strong_match=False,

            kb_mode=kb_mode,

            metadata={"diagnosis_type": diagnosis_type},

        )



    def _online_route(

        self,

        prompt: str,

        task: TaskType,

        start: float,

        kb_mode: Literal["semantic", "hash", "disabled"],

    ) -> IntelligentRouteResult:

        llm = self._route_completion(prompt, _SYSTEM_PROMPTS[task], task)

        latency = int((time.perf_counter() - start) * 1000)
        confidence = llm.confidence
        if llm.provider == "ollama":
            confidence = min(confidence, 0.45)

        return IntelligentRouteResult(

            content=llm.content,

            source=ResponseSource.ONLINE,

            provider=llm.provider,

            model=llm.model,

            confidence=confidence,

            task_type=task,

            similar_cases=[],

            latency_ms=latency,

            tokens_used=llm.tokens_used,

            used_online=True,

            kb_hits=0,

            strong_match=False,

            kb_mode=kb_mode,

        )



    def _provider_by_name(self, name: str) -> LLMProvider | None:
        return next((p for p in self.providers if p.name == name), None)

    @staticmethod
    def _is_useful_local_answer(content: str) -> bool:
        text = (content or "").strip()
        if len(text) < _MIN_USEFUL_LOCAL_ANSWER_CHARS:
            return False
        lowered = text.lower()
        return not any(marker in lowered for marker in _LOCAL_ANSWER_FALLBACK_MARKERS)

    def _diagnosis_combo(self, prompt: str, system: str) -> LLMResponse | None:
        """Ollama-first, cloud-checked diagnosis: combine when both have signal.

        Tries each configured verifier in `_DIAGNOSIS_VERIFIER_ORDER` (Groq
        before Gemini, since Groq's free tier allows far more requests/day)
        so a quota-exhausted verifier doesn't block the others.
        """
        verifiers = [
            provider
            for name in _DIAGNOSIS_VERIFIER_ORDER
            if (provider := self._provider_by_name(name)) is not None
            and provider.is_configured
        ]
        if not verifiers:
            return None

        ollama = self._provider_by_name("ollama")
        local_answer: str | None = None
        if ollama is not None and ollama.is_configured:
            try:
                # Short draft: the cloud verifier rewrites/expands this anyway,
                # so a full-length local answer would only add latency without
                # adding value — Ollama's generation time scales with tokens.
                local_result = ollama.complete(
                    prompt, system_prompt=system, max_tokens=_LOCAL_DRAFT_MAX_TOKENS
                )
                if self._is_useful_local_answer(local_result.content):
                    local_answer = local_result.content
            except Exception:
                logger.debug("Local Ollama pass failed before cloud combo", exc_info=True)

        combo_prompt = prompt
        if local_answer:
            combo_prompt = f"{prompt}{_DIAGNOSIS_SYNTHESIS_HINT}{local_answer}"

        for verifier in verifiers:
            try:
                result = verifier.complete(combo_prompt, system_prompt=system)
            except Exception:
                logger.warning(
                    "%s diagnosis combo failed, trying next verifier",
                    verifier.name,
                    exc_info=True,
                )
                continue
            if local_answer:
                result = result.model_copy(update={"provider": f"ollama+{verifier.name}"})
            return result
        return None

    def _route_completion(
        self, prompt: str, system: str, task: TaskType, *, allow_combo: bool = True
    ):
        """Pick a completion strategy: Ollama+Gemini combo for diagnosis, else the
        plain provider fallback chain."""
        if allow_combo and task == TaskType.DIAGNOSIS:
            combo = self._diagnosis_combo(prompt, system)
            if combo is not None:
                return combo
        return self._call_chain(prompt, system, task)

    def _call_chain(self, prompt: str, system: str, task: TaskType):

        last_error: Exception | None = None

        for provider in self._ordered_providers(task):

            try:

                return provider.complete(prompt, system_prompt=system)

            except Exception as exc:

                last_error = exc

                logger.warning("Provider %s failed: %s", provider.name, exc)

        from app.ai.providers.diagnostics import build_chat_fallback_message
        from app.ai.schemas import LLMResponse

        message = build_chat_fallback_message()
        if last_error:
            logger.error("All providers failed; last error: %s", last_error)
        return LLMResponse(
            provider="none",
            model="none",
            content=message,
            confidence=0.0,
        )



    def _ordered_providers(self, task: TaskType) -> list[LLMProvider]:

        preferred = _INTENT_PROVIDER_ORDER.get(task, ("gpt4", "ollama"))

        by_name = {provider.name: provider for provider in self.providers}

        ordered: list[LLMProvider] = []

        for name in preferred:

            provider = by_name.get(name)

            if provider and provider.is_configured:

                ordered.append(provider)

        for provider in sorted(self.providers, key=lambda p: p.priority):

            if provider not in ordered and provider.is_configured:

                ordered.append(provider)

        return ordered



    def _adjust_confidence(

        self,

        result: IntelligentRouteResult,

        diagnosis_type: str,

    ) -> IntelligentRouteResult:

        stats = self.learning.get_accuracy(diagnosis_type)

        accuracy = stats.get("accuracy", 0.0) if isinstance(stats, dict) else 0.0

        low_warning = False

        confidence = result.confidence

        if accuracy > 0.85:

            confidence = min(1.0, confidence + 0.1)

        elif 0 < accuracy < 0.5:

            confidence = max(0.0, confidence - 0.1)

            low_warning = True

        result.confidence = confidence

        result.low_accuracy_warning = low_warning

        return result



    def _finalize_route(

        self,

        result: IntelligentRouteResult,

        diagnosis_type: str,

    ) -> IntelligentRouteResult:

        cost = 0.0

        if result.used_online:

            cost = 0.001

        self.learning.record_route_event(

            diagnosis_type=diagnosis_type,

            kb_mode=result.kb_mode,

            strong_match=result.strong_match,

            used_online=result.used_online,

            provider=result.provider,

            latency_ms=result.latency_ms,

            cost_estimate=cost,

        )

        return result



    @staticmethod

    def _cache_key(prompt: str, task: TaskType, similar: list[KnowledgeCase]) -> str:

        similar_ids = ",".join(case.id for case in similar[:3])

        raw = f"{task.value}:{prompt}:{similar_ids}"

        return hashlib.sha256(raw.encode()).hexdigest()

