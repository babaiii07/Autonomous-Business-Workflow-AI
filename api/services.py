from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from tools.db import ApprovalRepository, LogRepository
from workflows.graph import execute_action, store_memory
from workflows.state import WorkflowState


def resume_from_approval(*, db: Session, approval_id: int) -> WorkflowState:
    approvals = ApprovalRepository(db)
    row = approvals.get(approval_id)
    if row is None:
        raise ValueError("Approval not found")
    if row.status not in {"approved", "rejected"}:
        raise ValueError("Approval still pending")
    if not row.context:
        raise ValueError("Approval context missing; cannot resume")

    state: WorkflowState = dict(row.context)  # type: ignore[assignment]
    state["approval_id"] = approval_id

    # Re-run the human_review logic implicitly by mapping decision based on approval status.
    mapped = "Approve" if row.status == "approved" else "Reject"
    decision = dict(state.get("decision") or {})
    decision["decision"] = mapped
    decision["reasoning"] = f"{(decision.get('reasoning') or '').strip()}\nHuman decision: {row.status}. Note: {row.review_note or ''}".strip()
    state["decision"] = decision

    # Continue with deterministic execution and memory write.
    state = execute_action(state)
    state = store_memory(state)
    return state

