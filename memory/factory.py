from __future__ import annotations

from config import get_settings

from .base import MemoryStore
from .inmemory_store import InMemoryStore
from .pinecone_store import PineconeStore


def get_memory_store() -> MemoryStore:
    """
    Production default: Pinecone when configured.
    Dev fallback: In-memory store when Pinecone is not configured.
    """

    settings = get_settings()
    if settings.pinecone_api_key:
        try:
            return PineconeStore()
        except Exception:
            return InMemoryStore()
    return InMemoryStore()

