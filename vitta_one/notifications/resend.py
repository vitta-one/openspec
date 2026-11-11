"""Backend-only Resend transport; acceptance never means inbox delivery."""
from dataclasses import dataclass
import os
import re

import httpx


@dataclass(frozen=True, slots=True)
class EmailDelivery:
    status: str
    message_id: str | None = None


def configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip() and os.getenv("RESEND_FROM_EMAIL", "").strip())


def valid_recipient(email: str) -> bool:
    from vitta_one.patient_portal.service import _valid_patient_email
    return isinstance(email, str) and _valid_patient_email(email.strip().lower())


def send(*, email: str, subject: str, html: str, text: str, idempotency_key: str) -> EmailDelivery:
    if not configured():
        return EmailDelivery("NOT_CONFIGURED")
    if not valid_recipient(email) or not re.fullmatch(r"[a-zA-Z0-9/_-]{1,256}", idempotency_key):
        return EmailDelivery("FAILED")
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post("https://api.resend.com/emails", headers={
                "Authorization": "Bearer " + os.environ["RESEND_API_KEY"].strip(),
                "Content-Type": "application/json", "Idempotency-Key": idempotency_key,
            }, json={"from": os.environ["RESEND_FROM_EMAIL"].strip(), "to": [email],
                     "subject": subject, "html": html, "text": text})
    except httpx.HTTPError:
        return EmailDelivery("UNKNOWN")
    if not 200 <= response.status_code < 300:
        return EmailDelivery("FAILED")
    try:
        message_id = response.json().get("id")
    except (ValueError, AttributeError):
        return EmailDelivery("UNKNOWN")
    if not isinstance(message_id, str) or not 1 <= len(message_id) <= 128:
        return EmailDelivery("UNKNOWN")
    return EmailDelivery("ACCEPTED", message_id)
