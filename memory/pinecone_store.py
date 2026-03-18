from __future__ import annotations

import datetime as dt
from typing import Any

from pinecone import Pinecone

from config import get_settings

from .base import MemoryQueryResult, MemoryRecord, MemoryStore
from .embeddings import SimpleHashEmbeddings


class PineconeStore(MemoryStore):
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY missing")
        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = self._pc.Index(settings.pinecone_index)
        self._namespace = settings.pinecone_namespace
        self._embedder = SimpleHashEmbeddings(dim=384)

    def upsert(self, record: MemoryRecord) -> None:
        vec = self._embedder.embed(record.text)
        metadata = dict(record.metadata)
        metadata.update(
            {
                "type": record.type,
                "text": record.text,
                "created_at": record.created_at.isoformat(),
            }
        )
        self._index.upsert(vectors=[{"id": record.id, "values": vec, "metadata": metadata}], namespace=self._namespace)

    def query(self, *, text: str, top_k: int = 5, filter: dict[str, Any] | None = None) -> list[MemoryQueryResult]:
        q = self._embedder.embed(text)
        pine_filter = filter or None
        res = self._index.query(
            vector=q,
            top_k=top_k,
            include_metadata=True,
            namespace=self._namespace,
            filter=pine_filter,
        )
        out: list[MemoryQueryResult] = []
        for match in (res.get("matches") or []):
            md = match.get("metadata") or {}
            created_at = md.get("created_at")
            try:
                created_dt = dt.datetime.fromisoformat(created_at) if isinstance(created_at, str) else dt.datetime.now(dt.timezone.utc)
            except ValueError:
                created_dt = dt.datetime.now(dt.timezone.utc)
            rec = MemoryRecord(
                id=str(match.get("id")),
                text=str(md.get("text") or ""),
                type=str(md.get("type") or "other"),
                metadata={k: v for k, v in md.items() if k not in {"text", "type", "created_at"}},
                created_at=created_dt,
            )
            out.append(MemoryQueryResult(record=rec, score=float(match.get("score") or 0.0)))
        return out

