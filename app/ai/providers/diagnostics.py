"""Provider availability diagnostics for status API and CLI."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.ai.providers.base import LLMProvider
from app.ai.providers.errors import (
    ACTIONS_IT,
    ErrorKind,
    classify_exception,
)
from app.ai.providers.key_validation import env_secret, key_present, key_shape_valid
from app.ai.providers.registry import load_providers
from app.config.env_loader import get_env_load_state

logger = logging.getLogger(__name__)

from app.ai.providers.ollama_support import ollama_model_installed


def probe_ollama(provider, *, live: bool = True) -> dict[str, Any]:
    env_var = provider.env_var or "ALPILAB_OLLAMA_URL"
    key_present_flag = bool(env_secret(env_var) or getattr(provider, "base_url", ""))
    key_shape_valid_flag = True
    base_url = provider.base_url
    model = provider.model

    if not live:
        return {
            "name": provider.name,
            "model": model,
            "key_present": key_present_flag,
            "key_shape_valid": key_shape_valid_flag,
            "available": False,
            "error_kind": "none",
            "latency_ms": None,
        }

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
        if not ollama_model_installed(base_url, model):
            return {
                "name": provider.name,
                "model": model,
                "key_present": key_present_flag,
                "key_shape_valid": key_shape_valid_flag,
                "available": False,
                "error_kind": "model_missing",
                "latency_ms": None,
            }
        start = time.perf_counter()
        result = provider.complete("ping", system_prompt="Reply OK.", max_tokens=32)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "name": provider.name,
            "model": model,
            "key_present": key_present_flag,
            "key_shape_valid": key_shape_valid_flag,
            "available": bool(result.content.strip()),
            "error_kind": "none" if result.content.strip() else "unreachable",
            "latency_ms": latency_ms,
        }
    except httpx.HTTPError as exc:
        return {
            "name": provider.name,
            "model": model,
            "key_present": key_present_flag,
            "key_shape_valid": key_shape_valid_flag,
            "available": False,
            "error_kind": classify_exception(exc),
            "latency_ms": None,
        }
    except Exception as exc:
        return {
            "name": provider.name,
            "model": model,
            "key_present": key_present_flag,
            "key_shape_valid": key_shape_valid_flag,
            "available": False,
            "error_kind": classify_exception(exc),
            "latency_ms": None,
        }


def probe_cloud_provider(provider: LLMProvider, *, live: bool = True) -> dict[str, Any]:
    env_var = provider.env_var
    present = key_present(env_var) if env_var else False
    shape_ok = key_shape_valid(env_var) if env_var else False

    if not present:
        return {
            "name": provider.name,
            "model": provider.model,
            "key_present": False,
            "key_shape_valid": False,
            "available": False,
            "error_kind": "missing_key",
            "latency_ms": None,
        }

    if env_var and not shape_ok:
        logger.warning(
            "Provider %s enabled but %s does not match the expected prefix",
            provider.name,
            env_var,
        )

    if not live:
        return {
            "name": provider.name,
            "model": provider.model,
            "key_present": True,
            "key_shape_valid": shape_ok,
            "available": shape_ok,
            "error_kind": "malformed_key" if not shape_ok else "none",
            "latency_ms": None,
        }

    start = time.perf_counter()
    try:
        result = provider.complete("ping", system_prompt="Reply OK.", max_tokens=32)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "name": provider.name,
            "model": provider.model,
            "key_present": True,
            "key_shape_valid": shape_ok,
            "available": bool(result.content.strip()),
            "error_kind": "none" if result.content.strip() else "unreachable",
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        error_kind: ErrorKind = classify_exception(exc)
        if not shape_ok and error_kind == "unreachable":
            error_kind = "malformed_key"
        return {
            "name": provider.name,
            "model": provider.model,
            "key_present": True,
            "key_shape_valid": shape_ok,
            "available": False,
            "error_kind": error_kind,
            "latency_ms": None,
        }


def build_provider_status(*, live: bool = True) -> dict[str, Any]:
    providers = load_providers()
    rows: list[dict[str, Any]] = []
    for provider in providers:
        if provider.name == "ollama":
            rows.append(probe_ollama(provider, live=live))
        else:
            rows.append(probe_cloud_provider(provider, live=live))

    cloud_available = any(
        row["available"] for row in rows if row["name"] != "ollama"
    )
    ollama_row = next((row for row in rows if row["name"] == "ollama"), None)
    ollama_available = bool(ollama_row and ollama_row["available"])

    if cloud_available:
        brain_mode = "cloud"
    elif ollama_available:
        brain_mode = "local_only"
    else:
        brain_mode = "unavailable"

    config = get_env_load_state()
    return {
        "config": config,
        "providers": rows,
        "online_available": cloud_available,
        "offline_mode": not cloud_available,
        "brain_mode": brain_mode,
    }


def build_chat_fallback_message(status: dict[str, Any] | None = None) -> str:
    status = status or build_provider_status(live=False)
    rows = status.get("providers", [])
    cloud_rows = [row for row in rows if row.get("name") != "ollama"]
    ollama_row = next((row for row in rows if row.get("name") == "ollama"), None)

    any_cloud_key = any(row.get("key_present") for row in cloud_rows)
    if not any_cloud_key and not (ollama_row and ollama_row.get("key_present")):
        return (
            "Nessuna chiave API configurata e Ollama non impostato. "
            "Crea un file `.env` accanto a ALPILAB AI.exe con almeno OPENAI_API_KEY "
            "oppure avvia Ollama e scarica il modello (ollama pull llama3.2)."
        )

    if cloud_rows and all(row.get("error_kind") == "missing_key" for row in cloud_rows):
        if ollama_row and ollama_row.get("error_kind") == "unreachable":
            return (
                "Ollama non è raggiungibile su questo PC. Avvia l'app Ollama e verifica "
                "che il servizio sia attivo, oppure aggiungi una chiave API cloud nel `.env`."
            )
        if ollama_row and ollama_row.get("error_kind") == "model_missing":
            model = ollama_row.get("model", "llama3.2")
            return (
                f"Ollama è attivo ma manca il modello `{model}`. "
                f"Esegui: ollama pull {model}"
            )

    rejected = [row for row in cloud_rows if row.get("key_present") and not row.get("available")]
    if rejected:
        kinds = {row.get("error_kind") for row in rejected}
        if kinds <= {"auth_failed", "malformed_key", "auth_key_format_unsupported"}:
            return (
                "Le chiavi API presenti nel `.env` sono state rifiutate o sembrano malformate. "
                "Controlla virgolette, spazi e che la chiave sia completa."
            )
        if "no_credit" in kinds:
            return (
                "I provider cloud hanno rifiutato la richiesta per credito o quota esaurita. "
                "Verifica il billing del provider oppure usa Ollama in locale."
            )

    if ollama_row and ollama_row.get("error_kind") == "model_missing":
        model = ollama_row.get("model", "llama3.2")
        return f"Scarica il modello Ollama mancante: `ollama pull {model}`."

    if ollama_row and ollama_row.get("error_kind") == "unreachable":
        return (
            "Ollama non risponde. Avvia Ollama, poi verifica con `ollama list` "
            "che il modello sia presente."
        )

    return (
        "Nessun provider AI disponibile al momento. Verifica `.env`, Ollama e la connessione, "
        "poi riprova."
    )
