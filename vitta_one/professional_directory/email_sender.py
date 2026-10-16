"""Server-only Resend adapter. Never log credentials, headers, or message bodies."""

from dataclasses import dataclass
from html import escape
import os
import secrets
from urllib.parse import urlparse

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


def send_patient_portal_invitation(
    *, name: str, email: str, code: str, activation_url: str, invitation_id: int
) -> EmailDelivery:
    """Send a consented one-time patient activation code without persisting it."""
    key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("RESEND_FROM_EMAIL", "").strip()
    parsed = urlparse(str(activation_url or ""))
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    secure_url = parsed.scheme == "https" or local_http
    if not key or not sender or not secure_url or not parsed.netloc:
        return EmailDelivery(status="NOT_CONFIGURED")
    body = (
        f"<p>Olá, {escape(name)}.</p>"
        "<p>A Recepção da clínica solicitou a ativação do seu acesso ao portal Vitta-One.</p>"
        f"<p>Abra <a href=\"{escape(activation_url, quote=True)}\">a página de ativação</a> e informe este código: "
        f"<strong><code>{escape(code)}</code></strong></p>"
        "<p>O código é de uso único e expira em 24 horas. Se você não solicitou este acesso, ignore esta mensagem.</p>"
    )
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Idempotency-Key": f"vitta-patient-invite/{invitation_id}/{secrets.token_hex(12)}",
    }
    payload = {
        "from": sender,
        "to": [email],
        "subject": "Ative seu acesso ao Vitta-One",
        "html": body,
    }
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post("https://api.resend.com/emails", headers=headers, json=payload)
    except httpx.HTTPError:
        return EmailDelivery(status="UNKNOWN")
    if not 200 <= response.status_code < 300:
        return EmailDelivery(status="FAILED")
    try:
        message_id = response.json().get("id")
    except (ValueError, AttributeError):
        return EmailDelivery(status="UNKNOWN")
    if not isinstance(message_id, str) or not message_id:
        return EmailDelivery(status="UNKNOWN")
    return EmailDelivery(status="ACCEPTED", message_id=message_id)
