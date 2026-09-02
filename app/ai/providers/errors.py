"""Shared provider error classification for diagnostics."""

from __future__ import annotations

import json
from typing import Any, Literal

ErrorKind = Literal[
    "missing_key",
    "malformed_key",
    "auth_failed",
    "auth_key_format_unsupported",
    "no_credit",
    "unreachable",
    "model_missing",
    "none",
]


ACTIONS_IT: dict[str, str] = {
    "missing_key": "Aggiungi la chiave nel file .env accanto all'eseguibile e riavvia ALPILAB AI.",
    "malformed_key": "Controlla che la chiave sia completa, senza virgolette o spazi extra.",
    "auth_failed": "La chiave è stata rifiutata dal provider: rigenerala dal portale del servizio.",
    "auth_key_format_unsupported": (
        "Google ha rifiutato la chiave nel formato AQ. con errore ACCESS_TOKEN_TYPE_UNSUPPORTED: "
        "il gateway generativelanguage.googleapis.com non la accetta per questo account/progetto "
        "(problema noto in rollout Google, non di ALPILAB). ALPILAB invia già la chiave con "
        "x-goog-api-key. Se AI Studio non emette più chiavi AIza, apri un ticket su Google AI "
        "Developers Forum o rigenera la chiave dal progetto cloud."
    ),
    "no_credit": "Credito o quota esauriti sul provider cloud: ricarica il billing.",
    "unreachable": "Rete o servizio non raggiungibile: verifica connessione e firewall.",
    "model_missing": (
        "Modello non disponibile: per Ollama scaricalo con `ollama pull <nome>`; "
        "per un provider cloud il modello configurato potrebbe essere stato dismesso, "
        "aggiorna il nome modello in config/llm_providers.yaml."
    ),
    "none": "Provider operativo.",
}


def _collect_error_text(exc: BaseException) -> str:
    parts: list[str] = [str(exc), repr(exc)]
    for attr in ("message", "body", "response", "text"):
        value = getattr(exc, attr, None)
        if value is not None:
            parts.append(str(value))
    response = getattr(exc, "response", None)
    if response is not None:
        for attr in ("text", "body", "content", "reason"):
            value = getattr(response, attr, None)
            if value is not None:
                parts.append(str(value))
    return " ".join(parts)


def extract_status_code(exc: BaseException) -> int | None:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        code = getattr(response, "status_code", None)
        if isinstance(code, int):
            return code
    return None


def classify_error_text(message: str, *, status_code: int | None = None) -> ErrorKind:
    lower = message.lower()

    if "access_token_type_unsupported" in lower:
        return "auth_key_format_unsupported"

    if status_code == 401 or " 401" in lower or "unauthenticated" in lower:
        if "invalid api key" in lower or "incorrect api key" in lower or "api key" in lower:
            return "auth_failed"
        if "authentication" in lower or "credentials" in lower:
            return "auth_failed"
        return "auth_failed"

    if status_code == 403 or " 403" in lower or "permission denied" in lower:
        return "auth_failed"

    if (
        status_code in {402, 429}
        or "credit" in lower
        or "billing" in lower
        or "quota" in lower
        or "insufficient" in lower
        or "rate limit" in lower
        or "resource_exhausted" in lower
    ):
        return "no_credit"

    if (
        "connection refused" in lower
        or "connect error" in lower
        or "connection error" in lower
        or "name or service not known" in lower
        or "failed to establish a new connection" in lower
        or "network is unreachable" in lower
        or "timed out" in lower
        or "timeout" in lower
        or "temporarily unavailable" in lower
    ):
        return "unreachable"

    if status_code and status_code >= 500:
        return "unreachable"

    if "model" in lower and (
        "not found" in lower
        or "missing" in lower
        or "pull" in lower
        or "no longer available" in lower
    ):
        return "model_missing"

    if status_code == 404:
        return "model_missing"

    if status_code and 400 <= status_code < 500:
        return "auth_failed"

    return "unreachable"


def classify_exception(exc: BaseException) -> ErrorKind:
    name = exc.__class__.__name__.lower()
    message = _collect_error_text(exc)
    status_code = extract_status_code(exc)

    if "authentication" in name or "autherror" in name or "permissiondenied" in name:
        return classify_error_text(message, status_code=status_code or 401)

    return classify_error_text(message, status_code=status_code)


def parse_gemini_error_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return error
    return {}
