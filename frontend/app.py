from __future__ import annotations

import json

import requests
import streamlit as st

from config import get_settings


settings = get_settings()
BASE = settings.backend_base_url.rstrip("/")

st.set_page_config(page_title="AI COO Dashboard", layout="wide")
st.title("Autonomous Business Workflow AI (AI COO)")


def post_json(path: str, payload: dict):
    r = requests.post(f"{BASE}{path}", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def get_json(path: str):
    r = requests.get(f"{BASE}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


tab_run, tab_approvals, tab_history = st.tabs(["Run workflow", "Approvals", "Email history"])

with tab_run:
    st.subheader("Upload email / text")
    col1, col2 = st.columns(2)
    with col1:
        sender = st.text_input("Sender", value="vendor@example.com")
        subject = st.text_input("Subject", value="Invoice for March services")
    with col2:
        st.caption("Tip: include lines like `Invoice No: ABC-1234`, `Total: 1200.50`, `Tax: 120.00`, `Date: 2026-03-01` for the regex+LLM hybrid.")

    body = st.text_area("Email body", height=260, value="Hi,\n\nPlease find invoice details below:\nInvoice No: ABC-1234\nVendor: Example Vendor LLC\nDate: 2026-03-01\nTotal: 1200.50\nTax: 120.00\n\nThanks.")

    if st.button("Run AI COO workflow", type="primary"):
        with st.spinner("Running workflow..."):
            out = post_json("/workflows/run", {"sender": sender, "subject": subject, "body": body})
        st.success(f"Workflow status: {out['status']}")
        st.json(out)

        if out.get("approval_id"):
            st.info(f"Human approval required. Approval ID: {out['approval_id']}")

with tab_approvals:
    st.subheader("Pending approvals")
    if st.button("Refresh"):
        st.rerun()

    pending = []
    try:
        pending = get_json("/approvals/pending")
    except Exception as exc:
        st.error(f"Failed to load approvals: {exc}")

    if not pending:
        st.write("No pending approvals.")
    else:
        for a in pending:
            with st.expander(f"Approval #{a['id']} (email_id={a['email_id']})", expanded=False):
                st.write("**Requested reason**")
                st.write(a["requested_reason"])

                colA, colB = st.columns(2)
                reviewer = colA.text_input(f"Reviewer (#{a['id']})", value="finance.manager")
                note = colB.text_input(f"Note (#{a['id']})", value="")

                col1, col2, col3 = st.columns(3)
                if col1.button("Approve", key=f"approve_{a['id']}"):
                    post_json(f"/approvals/{a['id']}/review", {"status": "approved", "reviewer": reviewer, "review_note": note})
                    out = post_json(f"/workflows/resume/{a['id']}", {})
                    st.success("Approved and resumed.")
                    st.json(out)
                if col2.button("Reject", key=f"reject_{a['id']}"):
                    post_json(f"/approvals/{a['id']}/review", {"status": "rejected", "reviewer": reviewer, "review_note": note})
                    out = post_json(f"/workflows/resume/{a['id']}", {})
                    st.success("Rejected and resumed.")
                    st.json(out)
                if col3.button("Resume only", key=f"resume_{a['id']}"):
                    out = post_json(f"/workflows/resume/{a['id']}", {})
                    st.json(out)

with tab_history:
    st.subheader("Recent emails (from DB)")
    try:
        emails = get_json("/emails/recent")
        for e in emails:
            with st.expander(f"Email #{e['id']} from {e['sender']}"):
                st.write(f"**Subject:** {e.get('subject')}")
                st.write("**Body**")
                st.code(e["body"])
                st.write("**Parsed**")
                st.json(e.get("parsed") or {})
    except Exception as exc:
        st.error(f"Failed to load email history: {exc}")

