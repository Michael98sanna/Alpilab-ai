"""Anthropic Claude provider."""

from __future__ import annotations

import logging

from app.ai.providers.base import DEFAULT_TIMEOUT_SEC, LLMProvider
from app.ai.schemas import LLMResponse

logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    name = "claude"
    model = "claude-3-5-sonnet-20241022"
    env_var = "ANTHROPIC_API_KEY"

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.is_configured:
            raise RuntimeError("Claude provider not configured")

        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package not installed") from exc

        client = anthropic.Anthropic(api_key=self._api_key, timeout=DEFAULT_TIMEOUT_SEC)
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)
        text = ""
        if response.content:
            text = "".join(getattr(block, "text", "") for block in response.content)
        tokens = getattr(response.usage, "output_tokens", 0) + getattr(
            response.usage, "input_tokens", 0
        )
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=text.strip(),
            confidence=0.82,
            tokens_used=int(tokens),
        )
