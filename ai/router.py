"""Provider router for Alpilab AI."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Iterator
from enum import Enum

from ai.circuit_breaker import CircuitBreaker
from ai.prompt_cache import PromptCache
from ai.providers.base import AIProvider
from ai.providers.local import LocalAIProvider
from ai.providers.mock import MockProvider
from ai.schemas import AIRequest, AIResponse, ProviderCapability

logger = logging.getLogger(__name__)


class FallbackStrategy(str, Enum):
    """Provider selection strategy when multiple backends are configured."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    COST_OPTIMIZED = "cost_optimized"


class SmartAIRouter:
    """
    AI router with fallback, circuit breaker, cache, and rate limiting.

    Supports async generation; ``generate_sync`` wraps the same logic for
    synchronous callers.
    """

    DEFAULT_RATE_LIMIT_PER_HOUR = 1000

    def __init__(
        self,
        providers: list[AIProvider] | None = None,
        *,
        cache_ttl_sec: int = 3600,
        rate_limit_per_hour: int = DEFAULT_RATE_LIMIT_PER_HOUR,
        enable_rag: bool = True,
    ) -> None:
        self.providers = providers or [MockProvider()]
        self.enable_rag = enable_rag
        self.circuit_breakers = {
            provider.name: CircuitBreaker() for provider in self.providers
        }
        self.cache = PromptCache(ttl_sec=cache_ttl_sec)
        self.rate_limits = {
            provider.name: rate_limit_per_hour for provider in self.providers
        }
        self._request_timestamps: dict[str, list[float]] = {
            provider.name: [] for provider in self.providers
        }

    async def generate(
        self,
        request: AIRequest,
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
        use_cache: bool = True,
    ) -> AIResponse:
        """Generate an AI response with cache and provider fallback."""
        request = self._apply_rag_context(request)
        cached = self._get_cached_response(request, use_cache=use_cache)
        if cached is not None:
            return cached

        available = self._available_providers()
        if not available:
            return self._fallback_response(
                "Tutti i provider AI sono temporaneamente non disponibili.",
                error="No providers available",
            )

        if strategy == FallbackStrategy.PARALLEL:
            response = await self._try_parallel(request, available)
        elif strategy == FallbackStrategy.COST_OPTIMIZED:
            response = await self._try_sequential(
                request,
                sorted(available, key=lambda provider: getattr(provider, "cost_per_call", 0)),
            )
        else:
            response = await self._try_sequential(request, available)

        if use_cache and response.provider not in {"fallback"}:
            self.cache.set(request.prompt, response.content)
        return response

    def generate_sync(
        self,
        request: AIRequest,
        strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL,
        use_cache: bool = True,
    ) -> AIResponse:
        """Synchronous wrapper around ``generate``."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.generate(request, strategy=strategy, use_cache=use_cache))

        raise RuntimeError(
            "SmartAIRouter.generate_sync cannot run inside an active event loop; "
            "use await generate() instead."
        )

    def _apply_rag_context(self, request: AIRequest) -> AIRequest:
        """Augment the prompt with knowledge-base context when a symptom is provided."""
        if not self.enable_rag:
            return request

        symptom = request.symptom or request.metadata.get("symptom")
        if not symptom:
            return request

        from app.knowledge.knowledge_base import KnowledgeBase
        from app.models.database import SessionLocal

        db = SessionLocal()
        try:
            kb = KnowledgeBase(db)
            device = request.device or request.metadata.get("device")
            rag_context = kb.get_rag_context(str(symptom), device)
            if not rag_context:
                return request

            metadata = dict(request.metadata)
            metadata["rag_applied"] = True
            return request.model_copy(
                update={
                    "prompt": f"{rag_context}\n\nUtente: {request.prompt}",
                    "metadata": metadata,
                }
            )
        except Exception:
            logger.warning("RAG context lookup failed", exc_info=True)
            return request
        finally:
            db.close()

    async def _try_sequential(
        self,
        request: AIRequest,
        providers: list[AIProvider],
    ) -> AIResponse:
        for provider in providers:
            if not self._check_rate_limit(provider.name):
                continue

            try:
                response = await self._call_provider(provider, request)
                self._record_provider_success(provider.name)
                return response
            except Exception:
                self.circuit_breakers[provider.name].record_failure()
                continue

        return self._fallback_response(
            "Nessun provider ha potuto generare una risposta.",
            error="All providers failed",
        )

    async def _try_parallel(
        self,
        request: AIRequest,
        providers: list[AIProvider],
    ) -> AIResponse:
        eligible = [provider for provider in providers if self._check_rate_limit(provider.name)]
        if not eligible:
            return self._fallback_response(
                "Nessun provider disponibile entro i limiti di rate.",
                error="Rate limit exceeded",
            )

        async def _attempt(provider: AIProvider) -> tuple[AIProvider, AIResponse]:
            response = await self._call_provider(provider, request)
            return provider, response

        tasks = [asyncio.create_task(_attempt(provider)) for provider in eligible]
        try:
            for finished in asyncio.as_completed(tasks):
                try:
                    provider, response = await finished
                    self._record_provider_success(provider.name)
                    return response
                except Exception:
                    continue
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

        return self._fallback_response(
            "Nessun provider ha potuto generare una risposta.",
            error="All providers failed",
        )

    async def _call_provider(self, provider: AIProvider, request: AIRequest) -> AIResponse:
        if request.images:
            return await asyncio.to_thread(provider.generate_with_image, request)
        return await asyncio.to_thread(provider.generate, request)

    def _available_providers(self) -> list[AIProvider]:
        return [
            provider
            for provider in self.providers
            if provider.is_available()
            and self.circuit_breakers[provider.name].is_available()
        ]

    def _get_cached_response(
        self,
        request: AIRequest,
        *,
        use_cache: bool,
    ) -> AIResponse | None:
        if not use_cache or request.images:
            return None

        cached = self.cache.get(request.prompt)
        if cached is None:
            return None

        return AIResponse(
            content=cached,
            provider="cache",
            model="cache",
            finish_reason="cache_hit",
            metadata={"cached": True, "latency_ms": 0},
        )

    def _record_provider_success(self, provider_name: str) -> None:
        self.circuit_breakers[provider_name].record_success()
        self._record_request(provider_name)

    def _check_rate_limit(self, provider_name: str) -> bool:
        limit = self.rate_limits.get(provider_name, self.DEFAULT_RATE_LIMIT_PER_HOUR)
        now = time.time()
        hour_ago = now - 3600
        timestamps = [
            ts for ts in self._request_timestamps.get(provider_name, []) if ts > hour_ago
        ]
        self._request_timestamps[provider_name] = timestamps
        return len(timestamps) < limit

    def _record_request(self, provider_name: str) -> None:
        self._request_timestamps.setdefault(provider_name, []).append(time.time())

    @staticmethod
    def _fallback_response(text: str, *, error: str) -> AIResponse:
        return AIResponse(
            content=text,
            provider="fallback",
            model="fallback",
            finish_reason="error",
            metadata={"error": error},
        )


class AIRouter:
    """
    Selects an AI backend without exposing provider details to the application.

    Uses ``SmartAIRouter`` internally for cache, circuit breaking, and fallback.
    """

    def __init__(self, providers: list[AIProvider] | None = None) -> None:
        self._providers: list[AIProvider] = providers or self._default_providers()
        self._smart = SmartAIRouter(self._providers)
        self._default_provider = self._providers[0]

    @staticmethod
    def _default_providers() -> list[AIProvider]:
        local_url = os.getenv("ALPILAB_LOCAL_AI_URL", "").strip() or None
        return [MockProvider(), LocalAIProvider(local_url)]

    @property
    def provider_name(self) -> str:
        return self._default_provider.name

    @property
    def smart(self) -> SmartAIRouter:
        return self._smart

    def list_providers(self) -> list[str]:
        return [provider.name for provider in self._providers]

    def select_provider(self, request: AIRequest) -> AIProvider:
        """Pick the best available provider for a request (simple logic for now)."""
        if request.images:
            for provider in self._providers:
                if (
                    provider.is_available()
                    and ProviderCapability.IMAGE_INPUT in provider.capabilities()
                ):
                    return provider

        for provider in self._providers:
            if (
                provider.name == "local"
                and provider.is_available()
                and ProviderCapability.LOCAL in provider.capabilities()
            ):
                return provider

        for provider in self._providers:
            if provider.is_available():
                return provider

        return self._default_provider

    def generate(self, request: AIRequest) -> AIResponse:
        if request.images:
            provider = self.select_provider(request)
            return provider.generate_with_image(request)

        try:
            return self._smart.generate_sync(request)
        except RuntimeError:
            return self._generate_sync_fallback(request)

    def _generate_sync_fallback(self, request: AIRequest) -> AIResponse:
        """Sequential fallback when called from within a running event loop."""
        request = self._smart._apply_rag_context(request)
        cached = self._smart._get_cached_response(request, use_cache=True)
        if cached is not None:
            return cached

        for provider in self._smart._available_providers():
            if not self._smart._check_rate_limit(provider.name):
                continue
            try:
                response = provider.generate(request)
                self._smart._record_provider_success(provider.name)
                self._smart.cache.set(request.prompt, response.content)
                return response
            except Exception:
                self._smart.circuit_breakers[provider.name].record_failure()

        return SmartAIRouter._fallback_response(
            "Nessun provider ha potuto generare una risposta.",
            error="All providers failed",
        )

    def generate_stream(self, request: AIRequest) -> Iterator[str]:
        provider = self.select_provider(request)
        return provider.generate_stream(request)

    def ask(self, prompt: str) -> str:
        """Convenience helper for simple text prompts."""
        response = self.generate(AIRequest(prompt=prompt))
        return response.content
