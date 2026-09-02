"""Perplexity online search provider."""

from __future__ import annotations

import httpx

from app.ai.providers.base import DEFAULT_TIMEOUT_SEC, LLMProvider
from app.ai.schemas import LLMResponse


class PerplexityProvider(LLMProvider):
    name = "perplexity"
    model = "sonar"
    env_var = "PERPLEXITY_API_KEY"

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.is_configured:
            raise RuntimeError("Perplexity provider not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC) as client:
            response = client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            payload = response.json()

        choice = payload["choices"][0]["message"]["content"]
        tokens = payload.get("usage", {}).get("total_tokens", 0)
        citations = payload.get("citations") or []
        if not citations and isinstance(payload["choices"][0].get("message"), dict):
            citations = payload["choices"][0]["message"].get("citations") or []
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=str(choice).strip(),
            confidence=0.74,
            tokens_used=int(tokens),
            citations=[str(c) for c in citations if c],
        )
