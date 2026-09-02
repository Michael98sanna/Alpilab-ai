"""API key presence/shape checks — never log or return secret values."""

from __future__ import annotations

import os
import re

KEY_ENV_VARS: dict[str, str] = {
    "claude": "ANTHROPIC_API_KEY",
    "gpt4": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
}

EXPECTED_PREFIXES: dict[str, str] = {
    "ANTHROPIC_API_KEY": "sk-ant-",
    "OPENAI_API_KEY": "sk-",
    "GROQ_API_KEY": "gsk_",
    "PERPLEXITY_API_KEY": "pplx-",
}

GOOGLE_KEY_PREFIXES: tuple[str, ...] = ("AIza", "AQ.")

SECRET_PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{8,}"),
    re.compile(r"AQ\.[A-Za-z0-9._-]{8,}"),
    re.compile(r"gsk_[A-Za-z0-9_-]{8,}"),
    re.compile(r"pplx-[A-Za-z0-9_-]{8,}"),
)


def normalize_secret(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in "\"'":
        cleaned = cleaned[1:-1].strip()
    return cleaned


def read_env_secret(value: str | None) -> str:
    return normalize_secret(value)


def env_secret(env_var: str) -> str:
    return read_env_secret(os.getenv(env_var, ""))


def key_present(env_var: str) -> bool:
    return bool(env_secret(env_var))


def google_key_shape_valid(value: str) -> bool:
    return any(value.startswith(prefix) for prefix in GOOGLE_KEY_PREFIXES)


def key_shape_valid(env_var: str) -> bool:
    value = env_secret(env_var)
    if not value:
        return False
    if env_var == "GOOGLE_API_KEY":
        return google_key_shape_valid(value)
    prefix = EXPECTED_PREFIXES.get(env_var)
    if prefix is None:
        return True
    return value.startswith(prefix)


def assert_no_secrets_in_text(text: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise AssertionError("Serialized output must not contain API key material")
