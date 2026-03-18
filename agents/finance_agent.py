from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from tools.memory_tool import retrieve_context

from .json_utils import safe_json_loads
from .llm import get_chat_model
from .prompts import FINANCE_AGENT_PROMPT


def run_finance_analysis(*, invoice: dict[str, Any], email_context: dict[str, Any], memory_hits: list[dict[str, Any]]) -> dict[str, Any]:
    llm = get_chat_model()
    payload = {
        "invoice": invoice,
        "email_context": email_context,
        "memory_hits": memory_hits,
    }
    res = llm.invoke(
        [
            SystemMessage(content=FINANCE_AGENT_PROMPT),
            HumanMessage(content=f"{json.dumps(payload, ensure_ascii=False)}\n\nReturn ONLY valid JSON."),
        ]
    )
    content = getattr(res, "content", str(res))
    return safe_json_loads(content)

