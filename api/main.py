from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from config import get_settings
from tools.db import ApprovalRepository, EmailRepository, init_db
from utils import init_logging
from workflows import build_workflow_graph

from .deps import get_db
from .schemas import (
    ApprovalOut,
    ApprovalReviewRequest,
    EmailOut,
    WorkflowRunRequest,
    WorkflowRunResponse,
)
from .services import resume_from_approval


settings = get_settings()
init_logging(settings.log_level)
init_db()

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.api_rate_limit_per_minute}/minute"])

app = FastAPI(title="AI COO - Autonomous Business Workflow", version="1.0.0")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


graph = build_workflow_graph()


@app.get("/health")
@limiter.limit("60/minute")
def health(_: Request):
    return {"ok": True, "env": settings.env}


@app.post("/workflows/run", response_model=WorkflowRunResponse)
@limiter.limit("30/minute")
def run_workflow(req: Request, payload: WorkflowRunRequest):
    try:
        state = graph.invoke({"sender": payload.sender, "subject": payload.subject, "body": payload.body})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return WorkflowRunResponse(
        status=state.get("status") or ("needs_approval" if state.get("approval_id") else "completed"),
        email_id=state.get("email_id"),
        invoice_id=state.get("invoice_id"),
        decision_id=state.get("decision_id"),
        approval_id=state.get("approval_id"),
        parsed_email=state.get("parsed_email"),
        invoice=state.get("invoice"),
        memory_hits=state.get("memory_hits") or [],
        finance=state.get("finance"),
        decision=state.get("decision"),
        action_result=state.get("action_result"),
        error=state.get("error"),
    )


@app.get("/approvals/pending", response_model=list[ApprovalOut])
@limiter.limit("60/minute")
def list_pending(req: Request, db: Session = Depends(get_db)):
    rows = ApprovalRepository(db).list_pending(limit=200)
    return [
        ApprovalOut(
            id=r.id,
            email_id=r.email_id,
            invoice_id=r.invoice_id,
            decision_id=r.decision_id,
            status=r.status,
            requested_reason=r.requested_reason,
            reviewer=r.reviewer,
            review_note=r.review_note,
        )
        for r in rows
    ]


@app.post("/approvals/{approval_id}/review", response_model=ApprovalOut)
@limiter.limit("30/minute")
def review_approval(req: Request, approval_id: int, payload: ApprovalReviewRequest, db: Session = Depends(get_db)):
    repo = ApprovalRepository(db)
    try:
        row = repo.set_status(
            approval_id=approval_id,
            status=payload.status,
            reviewer=payload.reviewer,
            review_note=payload.review_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ApprovalOut(
        id=row.id,
        email_id=row.email_id,
        invoice_id=row.invoice_id,
        decision_id=row.decision_id,
        status=row.status,
        requested_reason=row.requested_reason,
        reviewer=row.reviewer,
        review_note=row.review_note,
    )


@app.post("/workflows/resume/{approval_id}", response_model=WorkflowRunResponse)
@limiter.limit("30/minute")
def resume_workflow(req: Request, approval_id: int, db: Session = Depends(get_db)):
    try:
        state = resume_from_approval(db=db, approval_id=approval_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return WorkflowRunResponse(
        status=state.get("status") or "completed",
        email_id=state.get("email_id"),
        invoice_id=state.get("invoice_id"),
        decision_id=state.get("decision_id"),
        approval_id=state.get("approval_id"),
        parsed_email=state.get("parsed_email"),
        invoice=state.get("invoice"),
        memory_hits=state.get("memory_hits") or [],
        finance=state.get("finance"),
        decision=state.get("decision"),
        action_result=state.get("action_result"),
        error=state.get("error"),
    )


@app.get("/emails/recent", response_model=list[EmailOut])
@limiter.limit("60/minute")
def recent_emails(req: Request, db: Session = Depends(get_db)):
    rows = EmailRepository(db).list_recent(limit=100)
    return [EmailOut(id=e.id, sender=e.sender, subject=e.subject, body=e.body, parsed=e.parsed) for e in rows]

