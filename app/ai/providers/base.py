"""Abstract LLM provider for the ALPILAB Brain."""

from __future__ import annotations

import logging
import os
import time
from abc import ABC, abstractmethod

from app.ai.providers.key_validation import read_env_secret
from app.ai.schemas import LLMResponse

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SEC = 30.0


class LLMProvider(ABC):
    """Provider interface used by BrainRouter."""

    name: str = "unknown"
    model: str = ""
    env_var: str = ""
    cost_per_1k: float = 0.0
    priority: int = 50

    def __init__(self, *, model: str | None = None, enabled: bool = True) -> None:
        self.model = model or self.model
        self._enabled = enabled
        raw = os.getenv(self.env_var, "") if self.env_var else ""
        self._api_key = read_env_secret(raw) if self.env_var else ""

    @property
    def is_configured(self) -> bool:
        if not self._enabled:
            return False
        if self.name == "ollama":
            return True
        return bool(self._api_key)

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a completion."""

    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            response = self.complete("ping", system_prompt="Reply with OK.", max_tokens=256)
            return bool(response.content.strip())
        except Exception:
            logger.debug("Health check failed for %s", self.name, exc_info=True)
            return False

    def _timed_complete(
        self,
        fn,
        *,
        provider: str,
        model: str,
    ) -> LLMResponse:
        start = time.perf_counter()
        content = fn()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return LLMResponse(
            provider=provider,
            model=model,
            content=content,
            confidence=0.75,
            latency_ms=latency_ms,
        )
