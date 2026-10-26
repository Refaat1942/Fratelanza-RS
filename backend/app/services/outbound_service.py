"""Single gateway for every outbound email / WhatsApp / SMS.

* Demo tenants → ``suppressed_demo`` (mock sink). Nothing ever leaves the platform.
* OUTBOUND_MODE != "live" → ``logged`` only.
* live + email + SMTP configured → sent via SMTP. WhatsApp/SMS have no provider integration in
  this codebase yet, so they are ``logged`` with a note.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.rentals import OutboundMessage
from app.models.tenant import Company

logger = logging.getLogger(__name__)


def _is_demo_context(company: Optional[Company]) -> bool:
    if company is not None and company.is_demo:
        return True
    try:
        from app.middleware.module_guard import current_access

        ctx = current_access.get()
        return bool(ctx and ctx.is_demo)
    except Exception:  # pragma: no cover - defensive
        return False


def _send_smtp(recipient: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


class OutboundService:
    @staticmethod
    async def send(
        db: AsyncSession,
        company: Optional[Company],
        *,
        channel: str,
        recipient: str,
        subject: Optional[str] = None,
        body: str = "",
        dedupe_key: Optional[str] = None,
    ) -> OutboundMessage:
        if _is_demo_context(company):
            provider, status, error = "demo_sink", "suppressed_demo", None
        elif settings.OUTBOUND_MODE != "live":
            provider, status, error = "log", "logged", None
        elif channel == "email" and settings.SMTP_HOST:
            provider = "smtp"
            try:
                await asyncio.to_thread(_send_smtp, recipient, subject or "", body)
                status, error = "sent", None
            except Exception as exc:  # delivery failures must not break the business transaction
                logger.warning("SMTP delivery failed: %s", exc)
                status, error = "failed", str(exc)[:500]
        else:
            provider, status, error = "log", "logged", f"no {channel} provider configured"
        message = OutboundMessage(
            company_id=company.id if company else None,
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            provider=provider,
            status=status,
            dedupe_key=dedupe_key,
            error=error,
        )
        db.add(message)
        await db.flush()
        return message
