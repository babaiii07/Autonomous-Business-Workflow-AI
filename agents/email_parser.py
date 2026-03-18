from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from .json_utils import safe_json_loads
from .llm import get_chat_model
from .prompts import EMAIL_PARSER_PROMPT


def run_email_parser(*, sender: str, subject: str | None, body: str) -> dict[str, Any]:
    llm = get_chat_model()
    payload = f"Email sender: {sender}\nSubject: {subject or ''}\n\nEmail body:\n{body}\n\nReturn ONLY valid JSON."
    res = llm.invoke([SystemMessage(content=EMAIL_PARSER_PROMPT), HumanMessage(content=payload)])
    content = getattr(res, "content", str(res))
    data = safe_json_loads(content)
    # Ensure sender is present and consistent.
    data.setdefault("sender", sender)
    return data

