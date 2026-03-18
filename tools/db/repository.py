from __future__ import annotations

import datetime as dt
from typing import Any, Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .models import ActionLog, Approval, Decision, Email, Invoice


class EmailRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, sender: str, subject: str | None, body: str, parsed: dict[str, Any] | None) -> Email:
        email = Email(sender=sender, subject=subject, body=body, parsed=parsed)
        self.session.add(email)
        self.session.commit()
        self.session.refresh(email)
        return email

    def get(self, email_id: int) -> Email | None:
        return self.session.get(Email, email_id)

    def list_recent(self, limit: int = 50) -> list[Email]:
        stmt: Select[tuple[Email]] = select(Email).order_by(Email.received_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())


class InvoiceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, email_id: int, extracted: dict[str, Any] | None) -> Invoice:
        invoice = Invoice(email_id=email_id, extracted=extracted)
        if extracted:
            invoice.invoice_number = extracted.get("invoice_number")
            invoice.vendor_name = extracted.get("vendor_name")
            invoice.amount = extracted.get("amount")
            invoice.tax = extracted.get("tax")
            invoice.line_items = extracted.get("line_items")
            inv_date = extracted.get("date")
            if isinstance(inv_date, str):
                try:
                    invoice.invoice_date = dt.date.fromisoformat(inv_date)
                except ValueError:
                    invoice.invoice_date = None
        self.session.add(invoice)
        self.session.commit()
        self.session.refresh(invoice)
        return invoice

    def get(self, invoice_id: int) -> Invoice | None:
        return self.session.get(Invoice, invoice_id)

    def find_by_number_vendor(self, *, invoice_number: str | None, vendor_name: str | None, limit: int = 10) -> list[Invoice]:
        if not invoice_number and not vendor_name:
            return []
        stmt = select(Invoice).order_by(Invoice.created_at.desc()).limit(limit)
        if invoice_number:
            stmt = stmt.where(Invoice.invoice_number == invoice_number)
        if vendor_name:
            stmt = stmt.where(Invoice.vendor_name == vendor_name)
        return list(self.session.execute(stmt).scalars().all())


class DecisionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        email_id: int,
        invoice_id: int | None,
        decision: str,
        reasoning: str,
        payload: dict[str, Any] | None,
    ) -> Decision:
        row = Decision(email_id=email_id, invoice_id=invoice_id, decision=decision, reasoning=reasoning, payload=payload)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def get(self, decision_id: int) -> Decision | None:
        return self.session.get(Decision, decision_id)


class ApprovalRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        email_id: int,
        invoice_id: int | None,
        decision_id: int | None,
        requested_reason: str,
        context: dict[str, Any] | None = None,
    ) -> Approval:
        row = Approval(
            email_id=email_id,
            invoice_id=invoice_id,
            decision_id=decision_id,
            requested_reason=requested_reason,
            context=context,
            status="pending",
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def get(self, approval_id: int) -> Approval | None:
        return self.session.get(Approval, approval_id)

    def list_pending(self, limit: int = 100) -> list[Approval]:
        stmt = select(Approval).where(Approval.status == "pending").order_by(Approval.created_at.asc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def set_status(
        self,
        *,
        approval_id: int,
        status: str,
        reviewer: str | None,
        review_note: str | None,
    ) -> Approval:
        row = self.session.get(Approval, approval_id)
        if row is None:
            raise ValueError("Approval not found")
        row.status = status
        row.reviewer = reviewer
        row.review_note = review_note
        row.reviewed_at = dt.datetime.now(dt.timezone.utc)
        self.session.commit()
        self.session.refresh(row)
        return row


class LogRepository:
    def __init__(self, session: Session):
        self.session = session

    def log(self, *, email_id: int, invoice_id: int | None, action_type: str, success: bool, details: dict[str, Any] | None) -> ActionLog:
        row = ActionLog(email_id=email_id, invoice_id=invoice_id, action_type=action_type, success=success, details=details)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_for_email(self, email_id: int, limit: int = 200) -> list[ActionLog]:
        stmt = select(ActionLog).where(ActionLog.email_id == email_id).order_by(ActionLog.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

