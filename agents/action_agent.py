from __future__ import annotations

from typing import Any

from tools.email import EmailClient


def run_actions(*, decision: str, email_sender: str, invoice: dict[str, Any] | None) -> dict[str, Any]:
    """
    Deterministic execution layer (does not ask the LLM to actually "do" side effects).
    The LLM's role is upstream: parsing/extraction/analysis/decisioning.
    """

    client = EmailClient()

    if decision == "Approve":
        subject = "Invoice received - Approved"
        body = "Thanks — your invoice has been received and approved for processing."
        client.send(to=email_sender, subject=subject, body=body)
        return {"actions": ["send_email:approved"], "result": "Approval email sent."}

    if decision == "Reject":
        subject = "Invoice received - Rejected"
        body = "Thanks — your invoice was reviewed but could not be approved. Reply to this email with clarification."
        client.send(to=email_sender, subject=subject, body=body)
        return {"actions": ["send_email:rejected"], "result": "Rejection email sent."}

    subject = "Invoice received - Pending review"
    body = "Thanks — your invoice is pending internal review. We’ll respond shortly."
    client.send(to=email_sender, subject=subject, body=body)
    return {"actions": ["send_email:pending_review"], "result": "Pending-review email sent."}

