from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


DecisionLabel = Literal["Approve", "Reject", "Need human review"]


class WorkflowState(TypedDict, total=False):
    # Input
    sender: str
    subject: str | None
    body: str

    # Persisted entities
    email_id: int
    invoice_id: int | None
    decision_id: int | None
    approval_id: int | None

    # Agent outputs
    parsed_email: dict[str, Any]
    invoice: dict[str, Any] | None
    memory_hits: list[dict[str, Any]]
    finance: dict[str, Any] | None
    decision: dict[str, Any]  # {decision, reasoning}
    action_result: dict[str, Any] | None

    # Control
    status: Literal["completed", "needs_approval", "failed"]
    error: str | None

