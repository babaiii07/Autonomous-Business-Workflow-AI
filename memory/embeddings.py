from __future__ import annotations

import hashlib
from typing import Iterable, List


class SimpleHashEmbeddings:
    """
    Deterministic, dependency-light embeddings for demos/dev.

    Not SOTA, but ensures:
    - no external embedding API required
    - stable vectors for Pinecone/in-memory similarity
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        # Hash text into bytes, then expand deterministically.
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        out: list[float] = []
        idx = 0
        while len(out) < self.dim:
            chunk = hashlib.sha256(seed + bytes([idx])).digest()
            out.extend([(b / 255.0) * 2.0 - 1.0 for b in chunk])
            idx = (idx + 1) % 256
        return out[: self.dim]

    def embed_many(self, texts: Iterable[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

