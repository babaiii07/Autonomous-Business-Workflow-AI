from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    sender: str
    subject: str | None = None
    body: str


class WorkflowRunResponse(BaseModel):
    status: Literal["completed", "needs_approval", "failed"]
    email_id: int | None = None
    invoice_id: int | None = None
    decision_id: int | None = None
    approval_id: int | None = None
    parsed_email: dict[str, Any] | None = None
    invoice: dict[str, Any] | None = None
    memory_hits: list[dict[str, Any]] = Field(default_factory=list)
    finance: dict[str, Any] | None = None
    decision: dict[str, Any] | None = None
    action_result: dict[str, Any] | None = None
    error: str | None = None


class ApprovalReviewRequest(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer: str | None = None
    review_note: str | None = None


class ApprovalOut(BaseModel):
    id: int
    email_id: int
    invoice_id: int | None
    decision_id: int | None
    status: str
    requested_reason: str
    reviewer: str | None
    review_note: str | None


class EmailOut(BaseModel):
    id: int
    sender: str
    subject: str | None
    body: str
    parsed: dict[str, Any] | None

