"""Embedding helpers for knowledge-base indexing and search."""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

import numpy as np

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    """Minimal embedding interface."""

    def encode(self, text: str) -> np.ndarray:
        ...


class HashEmbedder:
    """Deterministic lightweight embedder for tests and offline fallback."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode(self, text: str) -> np.ndarray:
        tokens = re.findall(r"\w+", text.lower())
        vector = np.zeros(self.dimensions, dtype=np.float64)
        for token in tokens:
            vector[hash(token) % self.dimensions] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector


class LazySentenceTransformerEmbedder:
    """Lazy-loaded sentence-transformers backend."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, text: str) -> np.ndarray:
        model = self._get_model()
        return np.asarray(model.encode(text), dtype=np.float64)


def default_embedder() -> Embedder:
    try:
        import sentence_transformers  # noqa: F401

        return LazySentenceTransformerEmbedder()
    except ImportError:
        logger.info("sentence-transformers not installed; using HashEmbedder")
        return HashEmbedder()
