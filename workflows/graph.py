from __future__ import annotations

import datetime as dt
from typing import Any, Callable, Literal

from langgraph.graph import END, StateGraph

from agents import run_actions, run_decision, run_email_parser, run_finance_analysis, run_invoice_extractor
from config import get_settings
from tools.db import ApprovalRepository, DecisionRepository, EmailRepository, InvoiceRepository, LogRepository, SessionLocal, init_db
from tools.memory_tool import retrieve_context, serialize_for_memory, store_event
from utils import get_logger

from .state import WorkflowState


log = get_logger(component="workflow")


def _db_session():
    init_db()
    return SessionLocal()


def parse_email(state: WorkflowState) -> WorkflowState:
    parsed = run_email_parser(sender=state["sender"], subject=state.get("subject"), body=state["body"])
    with _db_session() as session:
        email = EmailRepository(session).create(
            sender=state["sender"],
            subject=state.get("subject"),
            body=state["body"],
            parsed=parsed,
        )
    # Store email in long-term memory (RAG)
    store_event(type="email", text=serialize_for_memory({"parsed": parsed, "body": state["body"]}), metadata={"email_id": email.id})
    return {**state, "parsed_email": parsed, "email_id": email.id}


def extract_invoice(state: WorkflowState) -> WorkflowState:
    intent = str((state.get("parsed_email") or {}).get("intent") or "other").lower()
    if intent != "invoice":
        return {**state, "invoice": None, "invoice_id": None}

    extracted = run_invoice_extractor(email_text=state["body"])
    with _db_session() as session:
        invoice = InvoiceRepository(session).create(email_id=state["email_id"], extracted=extracted)

    store_event(type="invoice", text=serialize_for_memory(extracted), metadata={"email_id": state["email_id"], "invoice_id": invoice.id})
    return {**state, "invoice": extracted, "invoice_id": invoice.id}


def retrieve_memory(state: WorkflowState) -> WorkflowState:
    query = (state.get("parsed_email") or {}).get("summary") or state["body"][:800]
    inv = state.get("invoice") or {}
    inv_no = inv.get("invoice_number")
    vendor = inv.get("vendor_name")
    if inv_no or vendor:
        query = f"{query}\nInvoiceNumber:{inv_no}\nVendor:{vendor}"

    hits = retrieve_context(query=query, top_k=5)
    return {**state, "memory_hits": hits}


def financial_analysis(state: WorkflowState) -> WorkflowState:
    inv = state.get("invoice")
    if not inv:
        return {**state, "finance": None}

    # Duplicate check: DB-level heuristic + memory hits already retrieved.
    with _db_session() as session:
        matches = InvoiceRepository(session).find_by_number_vendor(
            invoice_number=inv.get("invoice_number"),
            vendor_name=inv.get("vendor_name"),
            limit=5,
        )
    duplicate_hint = len(matches) > 1 or (len(matches) == 1 and matches[0].id != state.get("invoice_id"))

    finance = run_finance_analysis(invoice=inv, email_context=state.get("parsed_email") or {}, memory_hits=state.get("memory_hits") or [])
    finance.setdefault("anomalies", [])
    if duplicate_hint and "possible_duplicate" not in finance["anomalies"]:
        finance["anomalies"].append("possible_duplicate")

    # Minimal deterministic validations
    amount = inv.get("amount")
    if amount is None or (isinstance(amount, (int, float)) and amount <= 0):
        finance["anomalies"].append("invalid_or_missing_amount")
        finance["is_valid"] = False

    return {**state, "finance": finance}


def decision_node(state: WorkflowState) -> WorkflowState:
    decision = run_decision(
        email_context=state.get("parsed_email") or {},
        invoice=state.get("invoice"),
        finance=state.get("finance"),
        memory_hits=state.get("memory_hits") or [],
    )

    # Deterministic HITL rules layered on top.
    settings = get_settings()
    inv = state.get("invoice") or {}
    amount = inv.get("amount")
    anomalies = (state.get("finance") or {}).get("anomalies") or []
    if (isinstance(amount, (int, float)) and amount >= settings.high_value_threshold) or anomalies:
        decision["decision"] = "Need human review"
        if anomalies and "anomalies detected" not in decision.get("reasoning", ""):
            decision["reasoning"] = f"{decision.get('reasoning','').strip()}\nAnomalies: {anomalies}".strip()

    with _db_session() as session:
        row = DecisionRepository(session).create(
            email_id=state["email_id"],
            invoice_id=state.get("invoice_id"),
            decision=str(decision.get("decision") or "Need human review"),
            reasoning=str(decision.get("reasoning") or ""),
            payload=decision,
        )

    store_event(type="decision", text=serialize_for_memory(decision), metadata={"email_id": state["email_id"], "decision_id": row.id})
    return {**state, "decision": decision, "decision_id": row.id}


def human_review(state: WorkflowState) -> WorkflowState:
    """
    Creates/reads an approval record. If still pending, returns state that signals pause.
    """

    with _db_session() as session:
        approvals = ApprovalRepository(session)

        approval_id = state.get("approval_id")
        if approval_id:
            row = approvals.get(approval_id)
            if row and row.status == "pending":
                return {**state, "status": "needs_approval", "approval_id": row.id}
            if row and row.status in {"approved", "rejected"}:
                # Map human response to final decision.
                mapped = "Approve" if row.status == "approved" else "Reject"
                decision = dict(state.get("decision") or {})
                decision["decision"] = mapped
                decision["reasoning"] = f"{decision.get('reasoning','').strip()}\nHuman decision: {row.status}. Note: {row.review_note or ''}".strip()
                return {**state, "decision": decision}

        # Create new approval request with full context for resuming.
        row = approvals.create(
            email_id=state["email_id"],
            invoice_id=state.get("invoice_id"),
            decision_id=state.get("decision_id"),
            requested_reason=str((state.get("decision") or {}).get("reasoning") or "Human review requested."),
            context=dict(state),
        )
        return {**state, "status": "needs_approval", "approval_id": row.id}


def execute_action(state: WorkflowState) -> WorkflowState:
    decision_label = str((state.get("decision") or {}).get("decision") or "Need human review")
    res = run_actions(decision=decision_label, email_sender=state["sender"], invoice=state.get("invoice"))
    with _db_session() as session:
        LogRepository(session).log(
            email_id=state["email_id"],
            invoice_id=state.get("invoice_id"),
            action_type="execute_actions",
            success=True,
            details=res,
        )
    return {**state, "action_result": res}


def store_memory(state: WorkflowState) -> WorkflowState:
    payload = {
        "email_id": state.get("email_id"),
        "invoice_id": state.get("invoice_id"),
        "decision_id": state.get("decision_id"),
        "approval_id": state.get("approval_id"),
        "parsed_email": state.get("parsed_email"),
        "invoice": state.get("invoice"),
        "finance": state.get("finance"),
        "decision": state.get("decision"),
        "action_result": state.get("action_result"),
    }
    store_event(type="financial_summary", text=serialize_for_memory(payload), metadata={"email_id": state.get("email_id")})
    return {**state, "status": "completed"}


def should_human_review(state: WorkflowState) -> Literal["human_review", "execute_action"]:
    label = str((state.get("decision") or {}).get("decision") or "")
    if label == "Need human review":
        return "human_review"
    return "execute_action"


def build_workflow_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("parse_email", parse_email)
    graph.add_node("extract_invoice", extract_invoice)
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("financial_analysis", financial_analysis)
    graph.add_node("decision_node", decision_node)
    graph.add_node("human_review", human_review)
    graph.add_node("execute_action", execute_action)
    graph.add_node("store_memory", store_memory)

    graph.set_entry_point("parse_email")
    graph.add_edge("parse_email", "extract_invoice")
    graph.add_edge("extract_invoice", "retrieve_memory")
    graph.add_edge("retrieve_memory", "financial_analysis")
    graph.add_edge("financial_analysis", "decision_node")
    graph.add_conditional_edges("decision_node", should_human_review, {"human_review": "human_review", "execute_action": "execute_action"})
    graph.add_edge("human_review", END)  # pause on HITL
    graph.add_edge("execute_action", "store_memory")
    graph.add_edge("store_memory", END)

    return graph.compile()

