from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Any

from memory import MemoryRecord, get_memory_store


def store_event(*, type: str, text: str, metadata: dict[str, Any]) -> str:
    store = get_memory_store()
    rid = str(uuid.uuid4())
    store.upsert(
        MemoryRecord(
            id=rid,
            type=type,
            text=text,
            metadata=metadata,
            created_at=dt.datetime.now(dt.timezone.utc),
        )
    )
    return rid


def retrieve_context(*, query: str, top_k: int = 5, filter: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    store = get_memory_store()
    results = store.query(text=query, top_k=top_k, filter=filter)
    return [
        {
            "id": r.record.id,
            "type": r.record.type,
            "score": r.score,
            "text": r.record.text,
            "metadata": r.record.metadata,
            "created_at": r.record.created_at.isoformat(),
        }
        for r in results
    ]


def serialize_for_memory(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)

