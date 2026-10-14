"""Server-only Resend adapter. Never log credentials, headers, or message bodies."""

from dataclasses import dataclass
from html import escape
import os
import secrets

import httpx


@dataclass(frozen=True, slots=True)
class EmailDelivery:
    # ACCEPTED means provider HTTP acceptance, NOT inbox delivery.
    status: str
    message_id: str | None = None


def is_resend_configured() -> bool:
    return bool(os.environ.get("RESEND_API_KEY", "").strip()) and bool(
        os.environ.get("RESEND_FROM_EMAIL", "").strip()
    )


def send_medical_welcome(
    *, name: str, email: str, temporary_password: str, professional_id: int
) -> EmailDelivery:
    """Send a single temporary credential; never persist or auto-retry its plaintext."""
    key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("RESEND_FROM_EMAIL", "").strip()
    if not key or not sender:
        return EmailDelivery(status="NOT_CONFIGURED")

    # Escape untrusted profile values before interpolating into HTML.
    body = (
        f"<p>Olá, {escape(name)}.</p>"
        "<p>Seu acesso ao Vitta-One foi criado.</p>"
        f"<p>E-mail: <strong>{escape(email)}</strong></p>"
        f"<p>Senha temporária: <code>{escape(temporary_password)}</code></p>"
        "<p>Esta senha expira em 24 horas. No primeiro acesso será obrigatório "
        "escolher uma senha definitiva.</p>"
        "<p>Se você não solicitou esse acesso, avise a administração da clínica.</p>"
    )
    # Unique to this operation, no blind automatic retry after uncertain outcomes.
    idempotency_key = f"vitta-welcome/{professional_id}/{secrets.token_hex(12)}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    payload = {
        "from": sender,
        "to": [email],
        "subject": "Seu acesso ao Vitta-One",
        "html": body,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                "https://api.resend.com/emails", headers=headers, json=payload
            )
    except httpx.HTTPError:
        # Request might have reached the provider; never declare it unsent.
        return EmailDelivery(status="UNKNOWN")

    if not 200 <= response.status_code < 300:
        # Rejected requests are not described as successful.
        return EmailDelivery(status="FAILED")
    try:
        message_id = response.json().get("id")
    except (ValueError, AttributeError):
        return EmailDelivery(status="UNKNOWN")
    if not isinstance(message_id, str) or not message_id:
        return EmailDelivery(status="UNKNOWN")
    return EmailDelivery(status="ACCEPTED", message_id=message_id)
