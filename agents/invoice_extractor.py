from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from tools.invoice_parser import merge_invoice_extraction, regex_extract_invoice_fields

from .json_utils import safe_json_loads
from .llm import get_chat_model
from .prompts import INVOICE_EXTRACTION_PROMPT


def run_invoice_extractor(*, email_text: str) -> dict[str, Any]:
    llm = get_chat_model()
    regex_fields = regex_extract_invoice_fields(email_text)
    payload = f"Email/invoice text:\n{email_text}\n\nReturn ONLY valid JSON."
    res = llm.invoke([SystemMessage(content=INVOICE_EXTRACTION_PROMPT), HumanMessage(content=payload)])
    content = getattr(res, "content", str(res))
    llm_fields = safe_json_loads(content)
    return merge_invoice_extraction(regex_fields=regex_fields, llm_fields=llm_fields)

