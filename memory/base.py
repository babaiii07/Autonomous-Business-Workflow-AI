from __future__ import annotations

import abc
import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    text: str
    type: str  # invoice/decision/email/financial_summary/other
    metadata: dict[str, Any]
    created_at: dt.datetime


@dataclass(frozen=True)
class MemoryQueryResult:
    record: MemoryRecord
    score: float


class MemoryStore(abc.ABC):
    @abc.abstractmethod
    def upsert(self, record: MemoryRecord) -> None: ...

    @abc.abstractmethod
    def query(self, *, text: str, top_k: int = 5, filter: dict[str, Any] | None = None) -> list[MemoryQueryResult]: ...

