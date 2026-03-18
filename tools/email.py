from __future__ import annotations

import imaplib
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Iterable, Literal

from config import get_settings
from utils import get_logger


log = get_logger(component="email")


@dataclass(frozen=True)
class InboundEmail:
    sender: str
    subject: str | None
    body: str


class EmailClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def read_unseen(self, limit: int = 10) -> list[InboundEmail]:
        if self.settings.email_mode == "mock":
            return []
        return self._read_unseen_imap(limit=limit)

    def send(self, *, to: str, subject: str, body: str) -> None:
        if self.settings.email_mode == "mock":
            log.info("mock_email_send", to=to, subject=subject, body_preview=body[:200])
            return
        self._send_smtp(to=to, subject=subject, body=body)

    def _read_unseen_imap(self, limit: int) -> list[InboundEmail]:
        s = self.settings
        if not (s.imap_host and s.imap_user and s.imap_password):
            raise ValueError("IMAP config missing")

        mail = imaplib.IMAP4_SSL(s.imap_host)
        mail.login(s.imap_user, s.imap_password)
        mail.select("INBOX")
        typ, data = mail.search(None, "UNSEEN")
        if typ != "OK":
            return []
        ids = data[0].split()[-limit:]
        out: list[InboundEmail] = []
        for msg_id in ids:
            typ2, msg_data = mail.fetch(msg_id, "(RFC822)")
            if typ2 != "OK":
                continue
            raw = msg_data[0][1]
            # Minimal: treat as bytes -> string. Production should parse MIME properly.
            text = raw.decode(errors="ignore")
            out.append(InboundEmail(sender=s.imap_user, subject=None, body=text))
        mail.logout()
        return out

    def _send_smtp(self, *, to: str, subject: str, body: str) -> None:
        s = self.settings
        if not (s.smtp_host and s.smtp_user and s.smtp_password):
            raise ValueError("SMTP config missing")

        msg = EmailMessage()
        msg["From"] = s.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)
            server.send_message(msg)

