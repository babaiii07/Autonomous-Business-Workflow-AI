from __future__ import annotations

import json
from typing import Any


def safe_json_loads(text: str) -> dict[str, Any]:
    """
    Best-effort JSON parsing for LLM outputs.
    - Strips code fences
    - Extracts first {...} block if extra text exists
    """

    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
        # remove optional language hint line
        if "\n" in t:
            first, rest = t.split("\n", 1)
            if first.lower().strip() in {"json", "javascript"}:
                t = rest.strip()

    if not t.startswith("{"):
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            t = t[start : end + 1]
    return json.loads(t)

