"""Google Gemini provider via native Generative Language REST API."""

from __future__ import annotations

import httpx

from app.ai.providers.base import DEFAULT_TIMEOUT_SEC, LLMProvider
from app.ai.providers.errors import classify_error_text, parse_gemini_error_payload
from app.ai.schemas import LLMResponse

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiAPIError(RuntimeError):
    """Gemini HTTP error with response metadata for diagnostics."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


class GeminiProvider(LLMProvider):
    name = "gemini"
    model = "gemini-2.0-flash"
    env_var = "GOOGLE_API_KEY"

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self.is_configured:
            raise RuntimeError("Gemini provider not configured")

        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        url = f"{GEMINI_API_BASE}/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self._api_key, "Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT_SEC) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise GeminiAPIError(str(exc)) from exc

        if response.status_code >= 400:
            error_payload = parse_gemini_error_payload(response.text)
            message = str(error_payload.get("message") or response.text or response.reason_phrase)
            details = error_payload.get("details") or []
            reason = None
            if isinstance(details, list):
                for item in details:
                    if isinstance(item, dict) and item.get("reason"):
                        reason = str(item["reason"])
                        break
            kind = classify_error_text(
                f"{message} {reason or ''}",
                status_code=response.status_code,
            )
            raise GeminiAPIError(
                f"{message} {reason}".strip() if reason else message,
                status_code=response.status_code,
                reason=reason or kind,
            ) from None

        data = response.json()
        candidates = data.get("candidates") or []
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))

        usage = data.get("usageMetadata") or {}
        tokens = int(usage.get("totalTokenCount") or 0)
        return LLMResponse(
            provider=self.name,
            model=self.model,
            content=text.strip(),
            confidence=0.76,
            tokens_used=tokens,
        )
