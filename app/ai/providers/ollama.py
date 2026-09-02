"""Ollama local LLM provider (offline fallback)."""

from __future__ import annotations

import logging
import os

import httpx

from app.ai.providers.base import LLMProvider
from app.ai.providers.ollama_support import ollama_model_installed
from app.ai.schemas import LLMResponse

logger = logging.getLogger(__name__)

LOCAL_MODEL_MAX_CONFIDENCE = 0.45
# Local generation on modest hardware can take much longer than a cloud call;
# Ollama has no per-call cost, so it can afford a generous timeout.
OLLAMA_TIMEOUT_SEC = 120.0


class OllamaProvider(LLMProvider):
    name = "ollama"
    model = "llama3.2"
    env_var = "ALPILAB_OLLAMA_URL"

    @property
    def base_url(self) -> str:
        return (
            self._api_key
            or os.getenv("ALPILAB_OLLAMA_URL", "").strip()
            or "http://127.0.0.1:11434"
        ).rstrip("/")

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            with httpx.Client(timeout=OLLAMA_TIMEOUT_SEC) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
            content = str(data.get("response", "")).strip()
            confidence = LOCAL_MODEL_MAX_CONFIDENCE
        except Exception:
            from app.ai.providers.diagnostics import build_chat_fallback_message

            content = build_chat_fallback_message()
            confidence = 0.0

        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=content,
            confidence=min(confidence, LOCAL_MODEL_MAX_CONFIDENCE),
            tokens_used=0,
        )

    def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            if not ollama_model_installed(self.base_url, self.model):
                return False
            response = self.complete("ping", system_prompt="Reply with OK.", max_tokens=256)
            return bool(response.content.strip())
        except Exception:
            logger.debug("Ollama health check failed", exc_info=True)
            return False
