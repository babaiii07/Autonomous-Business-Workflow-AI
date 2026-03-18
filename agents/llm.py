from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from config import get_settings
from utils import get_logger


log = get_logger(component="llm")


@dataclass
class _ChatResult:
    content: str


class RuleBasedFallbackChatModel:
    """
    Minimal, deterministic fallback when GROQ_API_KEY is not configured.

    This avoids the "rotating responses" problem of FakeListChatModel when the workflow
    conditionally skips nodes (e.g., no invoice extraction for non-invoice emails).
    """

    def invoke(self, messages: Iterable[Any], **_: Any) -> _ChatResult:  # LangChain-compatible surface
        sys = ""
        user = ""
        for m in messages:
            c = getattr(m, "content", "")
            t = type(m).__name__.lower()
            if "system" in t:
                sys = str(c)
            elif "human" in t:
                user = str(c)

        sys_l = sys.lower()
        if "email understanding agent" in sys_l:
            return _ChatResult(
                content='{"sender": null, "intent": "other", "urgency": "low", "key_entities": [], "summary": "LLM not configured; cannot safely infer intent."}'
            )
        if "invoice processing expert" in sys_l:
            return _ChatResult(
                content='{"invoice_number": null, "vendor_name": null, "date": null, "amount": null, "tax": null, "line_items": []}'
            )
        if "financial analyst ai" in sys_l:
            return _ChatResult(
                content='{"is_valid": false, "category": "unknown", "anomalies": ["LLM not configured"], "recommendation": "Need human review"}'
            )
        if "business decision-making ai" in sys_l:
            return _ChatResult(
                content='{"decision": "Need human review", "reasoning": "LLM not configured; cannot decide safely."}'
            )
        if "execution agent" in sys_l:
            return _ChatResult(content='{"actions": [], "result": "No actions executed (LLM not configured)."}')

        return _ChatResult(content="{}")


def get_chat_model():
    """
    Returns Groq chat model when configured.
    Falls back to a safe fake model for local bootstrapping when no API key is present.
    """

    settings = get_settings()
    if settings.groq_api_key:
        from langchain_groq import ChatGroq  # type: ignore

        return ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=0)

    return RuleBasedFallbackChatModel()

