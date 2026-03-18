from __future__ import annotations

import re
from typing import Any


_INVOICE_NUMBER_RE = re.compile(r"(?:invoice\s*(?:no\.?|number)?\s*[:#]?\s*)([A-Z0-9-]{4,})", re.IGNORECASE)
_AMOUNT_RE = re.compile(r"(?:total\s*(?:amount)?\s*[:$]?\s*)(\d+(?:\.\d{1,2})?)", re.IGNORECASE)
_TAX_RE = re.compile(r"(?:tax\s*[:$]?\s*)(\d+(?:\.\d{1,2})?)", re.IGNORECASE)
_DATE_RE = re.compile(r"(?:date\s*[:]?[\s]*)(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
_VENDOR_RE = re.compile(r"(?:vendor|from)\s*[:]?[\s]*([A-Za-z0-9 &.,-]{2,})", re.IGNORECASE)


def regex_extract_invoice_fields(text: str) -> dict[str, Any]:
    invoice_number = _INVOICE_NUMBER_RE.search(text)
    amount = _AMOUNT_RE.search(text)
    tax = _TAX_RE.search(text)
    date = _DATE_RE.search(text)
    vendor = _VENDOR_RE.search(text)

    return {
        "invoice_number": invoice_number.group(1) if invoice_number else None,
        "vendor_name": vendor.group(1).strip() if vendor else None,
        "date": date.group(1) if date else None,
        "amount": float(amount.group(1)) if amount else None,
        "tax": float(tax.group(1)) if tax else None,
    }


def merge_invoice_extraction(*, regex_fields: dict[str, Any], llm_fields: dict[str, Any]) -> dict[str, Any]:
    """
    Hybrid extraction: prefer LLM for structured items (line_items), but keep regex when LLM is uncertain.
    """

    out: dict[str, Any] = {}
    for key in {"invoice_number", "vendor_name", "date", "amount", "tax", "line_items"}:
        llm_val = llm_fields.get(key) if llm_fields else None
        reg_val = regex_fields.get(key) if regex_fields else None
        out[key] = llm_val if llm_val not in (None, "", []) else reg_val
    return out

