"""Groq provider — free tier with high request/token limits (OpenAI-compatible API)."""

from __future__ import annotations

from app.ai.providers.base import DEFAULT_TIMEOUT_SEC, LLMProvider
from app.ai.schemas import LLMResponse

GROQ_API_BASE = "https://api.groq.com/openai/v1"


class GroqProvider(LLMProvider):
    name = "groq"
    model = "qwen/qwen3.8-27b"
    env_var = "GROQ_API_KEY"

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.is_configured:
            raise RuntimeError("Groq provider not configured")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package not installed") from exc

        client = OpenAI(api_key=self._api_key, base_url=GROQ_API_BASE, timeout=DEFAULT_TIMEOUT_SEC)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=choice.strip(),
            confidence=0.7,
            tokens_used=int(tokens),
        )
