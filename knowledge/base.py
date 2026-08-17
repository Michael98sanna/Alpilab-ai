"""Knowledge base abstractions — storage and retrieval come later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeDocument:
    """Lightweight document descriptor for a future KB / RAG pipeline."""

    title: str
    content: str
    id: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeBase(ABC):
    """Abstract knowledge store. Retrieval/RAG not implemented yet."""

    @abstractmethod
    def add_document(self, document: KnowledgeDocument) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, *, limit: int = 5) -> list[KnowledgeDocument]:
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        raise NotImplementedError


class MockKnowledgeBase(KnowledgeBase):
    """In-memory MOCK knowledge base for structural tests only."""

    def __init__(self) -> None:
        self._documents: list[KnowledgeDocument] = []

    def add_document(self, document: KnowledgeDocument) -> None:
        self._documents.append(document)

    def search(self, query: str, *, limit: int = 5) -> list[KnowledgeDocument]:
        q = query.lower().strip()
        if not q:
            return []
        matches = [
            doc
            for doc in self._documents
            if q in doc.title.lower() or q in doc.content.lower()
        ]
        return matches[:limit]

    def count(self) -> int:
        return len(self._documents)
