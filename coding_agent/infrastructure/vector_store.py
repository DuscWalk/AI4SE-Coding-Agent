# coding_agent/infrastructure/vector_store.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import math


@dataclass
class MemoryEntry:
    content: str
    embedding: list[float] | None = None


class VectorStore(ABC):
    @abstractmethod
    def search(self, query: str, query_embedding: list[float], top_k: int = 5) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def insert(self, text: str, embedding: list[float]) -> None:
        ...

    @abstractmethod
    def delete(self, text: str) -> None:
        ...


class InMemoryVectorStore(VectorStore):
    def __init__(self):
        self._entries: list[tuple[MemoryEntry, list[float]]] = []

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, query_embedding: list[float], top_k: int = 5) -> list[MemoryEntry]:
        if not self._entries:
            return []
        scored = [
            (entry, self._cosine_similarity(query_embedding, emb))
            for entry, emb in self._entries
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in scored[:top_k]]

    def insert(self, text: str, embedding: list[float]) -> None:
        self._entries.append((MemoryEntry(content=text, embedding=embedding), embedding))

    def delete(self, text: str) -> None:
        self._entries = [(e, emb) for e, emb in self._entries if e.content != text]