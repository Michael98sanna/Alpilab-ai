"""Knowledge base package (placeholder).

Future: technical manuals, repair history RAG, board schematics indexes.
No RAG implementation in this foundation phase.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeDocument:
    """Minimal document descriptor for a future knowledge base."""

    id: str
    title: str
    source: str
    tags: tuple[str, ...] = ()


class KnowledgeBase:
    """Placeholder knowledge base.

    Clearly marked as not implemented: search returns empty results.
    """

    def __init__(self) -> None:
        self._documents: list[KnowledgeDocument] = []

    def add(self, document: KnowledgeDocument) -> None:
        self._documents.append(document)

    def search(self, query: str, *, limit: int = 5) -> list[KnowledgeDocument]:
        # Foundation: no real indexing / embeddings.
        _ = query, limit
        return []

    @property
    def size(self) -> int:
        return len(self._documents)
