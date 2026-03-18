from __future__ import annotations

import math
from typing import Any

from .base import MemoryQueryResult, MemoryRecord, MemoryStore
from .embeddings import SimpleHashEmbeddings


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class InMemoryStore(MemoryStore):
    def __init__(self, *, dim: int = 384):
        self._embedder = SimpleHashEmbeddings(dim=dim)
        self._records: dict[str, MemoryRecord] = {}
        self._vectors: dict[str, list[float]] = {}

    def upsert(self, record: MemoryRecord) -> None:
        self._records[record.id] = record
        self._vectors[record.id] = self._embedder.embed(record.text)

    def query(self, *, text: str, top_k: int = 5, filter: dict[str, Any] | None = None) -> list[MemoryQueryResult]:
        q = self._embedder.embed(text)
        results: list[MemoryQueryResult] = []
        for rid, rec in self._records.items():
            if filter:
                ok = True
                for k, v in filter.items():
                    if rec.metadata.get(k) != v:
                        ok = False
                        break
                if not ok:
                    continue
            score = _cosine(q, self._vectors[rid])
            results.append(MemoryQueryResult(record=rec, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

