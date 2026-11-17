"""Backend-only Resend transport; acceptance never means inbox delivery."""
from dataclasses import dataclass
from email.utils import getaddresses
import os
import re

import httpx


@dataclass(frozen=True, slots=True)
class EmailDelivery:
    status: str
    message_id: str | None = None


def configured() -> bool:
    return bool(
        os.getenv("RESEND_API_KEY", "").strip()
        and valid_sender(os.getenv("RESEND_FROM_EMAIL", ""))
    )


def valid_recipient(email: str) -> bool:
    from vitta_one.patient_portal.service import _valid_patient_email
    if not isinstance(email, str):
        return False
    normalized = email.strip().lower()
    if not _valid_patient_email(normalized):
        return False
    domain = normalized.rsplit("@", 1)[1]
    return not (
        domain == "invalid"
        or domain.endswith((".invalid", ".test", ".example", ".localhost", ".local"))
    )


def valid_sender(value: str) -> bool:
    """Validate one safe sender address without claiming provider-domain verification."""
    raw = str(value or "").strip()
    if not raw or len(raw) > 320 or any(ord(char) < 32 for char in raw):
        return False
    if raw.count("<") > 1 or raw.count(">") > 1:
        return False
    parsed = getaddresses([raw])
    if len(parsed) != 1:
        return False
    display_name, address = parsed[0]
    if len(display_name) > 160 or not address or not valid_recipient(address):
        return False
    return True


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
            }, json={"from": os.environ["RESEND_FROM_EMAIL"].strip(), "to": [email.strip().lower()],
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
