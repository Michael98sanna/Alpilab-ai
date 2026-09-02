"""Load Brain LLM providers from YAML configuration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from app.ai.providers.base import LLMProvider
from app.ai.providers.claude import ClaudeProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.gpt4 import GPT4Provider
from app.ai.providers.groq import GroqProvider
from app.ai.providers.key_validation import env_secret, key_present, key_shape_valid
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.perplexity import PerplexityProvider

logger = logging.getLogger(__name__)

_PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "claude": ClaudeProvider,
    "gpt4": GPT4Provider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "perplexity": PerplexityProvider,
    "ollama": OllamaProvider,
}

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "llm_providers.yaml"


def load_providers(config_path: Path | None = None) -> list[LLMProvider]:
    """Instantiate enabled providers from YAML; skip missing API keys."""
    path = config_path or Path(os.getenv("ALPILAB_LLM_CONFIG", str(DEFAULT_CONFIG_PATH)))
    if not path.exists():
        logger.warning("LLM config not found at %s; only Ollama fallback may work", path)
        return [OllamaProvider(enabled=True)]

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    providers_cfg: dict[str, Any] = raw.get("providers", {})
    providers: list[LLMProvider] = []

    for name, cfg in sorted(
        providers_cfg.items(),
        key=lambda item: int(item[1].get("priority", 50)),
    ):
        if not cfg.get("enabled", True):
            continue
        cls = _PROVIDER_CLASSES.get(name)
        if cls is None:
            logger.warning("Unknown provider %s in config", name)
            continue

        env_var = getattr(cls, "env_var", "")
        if name != "ollama" and env_var:
            if not key_present(env_var):
                logger.warning(
                    "Provider %s disabilitato: variabile %s assente o vuota",
                    name,
                    env_var,
                )
                continue
            if not key_shape_valid(env_var):
                logger.warning(
                    "Provider %s abilitato ma %s sembra malformata (prefisso inatteso)",
                    name,
                    env_var,
                )

        provider = cls(
            model=cfg.get("model"),
            enabled=True,
        )
        provider.cost_per_1k = float(cfg.get("cost_per_1k", 0))
        provider.priority = int(cfg.get("priority", 50))
        if hasattr(provider, "capabilities"):
            provider.capabilities = list(cfg.get("capabilities", []))
        if provider.is_configured:
            providers.append(provider)
        else:
            logger.warning(
                "Provider %s disabilitato: variabile %s non impostata",
                name,
                getattr(provider, "env_var", "?"),
            )

    if not providers:
        logger.warning("Nessun provider cloud configurato; uso fallback Ollama/offline")
        providers.append(OllamaProvider(enabled=True))
    return providers
