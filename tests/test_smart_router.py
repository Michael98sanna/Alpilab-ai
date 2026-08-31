"""Tests for SmartAIRouter, circuit breaker, and prompt cache."""

from __future__ import annotations

import pytest

from ai.circuit_breaker import CircuitBreaker, CircuitState
from ai.prompt_cache import PromptCache
from ai.providers.failing import FailingProvider
from ai.providers.mock import MockProvider
from ai.router import FallbackStrategy, SmartAIRouter
from ai.schemas import AIRequest


@pytest.mark.asyncio
async def test_sequential_fallback() -> None:
    router = SmartAIRouter([FailingProvider(), MockProvider()])
    request = AIRequest(prompt="test")

    response = await router.generate(request, strategy=FallbackStrategy.SEQUENTIAL)

    assert response.content
    assert response.provider == "mock"


@pytest.mark.asyncio
async def test_prompt_cache() -> None:
    router = SmartAIRouter([MockProvider()])
    request = AIRequest(prompt="cache-test-unique")

    resp1 = await router.generate(request, use_cache=True)
    resp2 = await router.generate(request, use_cache=True)

    assert resp1.provider == "mock"
    assert resp2.provider == "cache"
    assert resp2.content == resp1.content


def test_circuit_breaker() -> None:
    breaker = CircuitBreaker(failure_threshold=3)
    assert breaker.is_available()

    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()

    assert not breaker.is_available()
    assert breaker.state == CircuitState.OPEN


def test_circuit_breaker_recovers_to_half_open() -> None:
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_sec=0)
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.is_available()
    assert breaker.state == CircuitState.HALF_OPEN


def test_prompt_cache_ttl_expiry() -> None:
    cache = PromptCache(ttl_sec=0)
    cache.set("prompt", "response")
    assert cache.get("prompt") is None


@pytest.mark.asyncio
async def test_cost_optimized_prefers_cheaper_provider() -> None:
    cheap = MockProvider()
    cheap.cost_per_call = 1
    expensive = FailingProvider()
    expensive.cost_per_call = 100

    router = SmartAIRouter([expensive, cheap])
    response = await router.generate(
        AIRequest(prompt="cost-test"),
        strategy=FallbackStrategy.COST_OPTIMIZED,
        use_cache=False,
    )

    assert response.provider == "mock"


@pytest.mark.asyncio
async def test_all_providers_unavailable_returns_fallback() -> None:
    router = SmartAIRouter([FailingProvider()])
    for _ in range(5):
        router.circuit_breakers["failing"].record_failure()

    response = await router.generate(
        AIRequest(prompt="unavailable"),
        use_cache=False,
    )

    assert response.provider == "fallback"
    assert "non disponibili" in response.content.lower()
