from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .json_utils import safe_json_loads
from .llm import get_chat_model
from .prompts import DECISION_AGENT_PROMPT


def run_decision(
    *,
    email_context: dict[str, Any],
    invoice: dict[str, Any] | None,
    finance: dict[str, Any] | None,
    memory_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    llm = get_chat_model()
    payload = {
        "email_context": email_context,
        "invoice": invoice,
        "finance": finance,
        "memory_hits": memory_hits,
        "instructions": "Return JSON with keys: decision (Approve/Reject/Need human review) and reasoning.",
    }
    res = llm.invoke(
        [
            SystemMessage(content=DECISION_AGENT_PROMPT),
            HumanMessage(content=f"{json.dumps(payload, ensure_ascii=False)}\n\nReturn ONLY valid JSON."),
        ]
    )
    content = getattr(res, "content", str(res))
    data = safe_json_loads(content)
    # Normalize decision label
    d = str(data.get("decision") or "").strip()
    if d.lower() in {"need review", "need human review", "review", "human review"}:
        data["decision"] = "Need human review"
    elif d.lower() == "approve":
        data["decision"] = "Approve"
    elif d.lower() == "reject":
        data["decision"] = "Reject"
    return data

