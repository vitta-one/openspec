"""Compatible access senders sharing the backend-only Resend transport."""
import secrets
from urllib.parse import urlparse

# Keep the existing public symbols and httpx patch surface compatible.
import httpx
from vitta_one.notifications.resend import EmailDelivery, configured, send
from vitta_one.notifications.templates import layout


def is_resend_configured() -> bool:
    return configured()


def send_medical_welcome(*, name: str, email: str, temporary_password: str, professional_id: int, token: str | None = None) -> EmailDelivery:
    """The temporary secret is transient; never persist this message body."""
    if token is not None:
        import reflex as rx
        from vitta_one.auth.authorization import require_role
        from vitta_one.auth.roles import Role
        from vitta_one.models.professional import Professional
        from vitta_one.models.auth import User
        from vitta_one.notifications.service import begin_access, finish_access
        with rx.session() as db:
            require_role(db, token, Role.ADMINISTRADOR)
            professional = db.get(Professional, professional_id)
            account = db.get(User, professional.user_id) if professional and professional.user_id else None
            if not account or account.email != email or not account.must_change_password:
                raise PermissionError("Envio de acesso não autorizado para este destinatário.")
            event = f"medical_access/{professional_id}/{account.temporary_password_expires_at.isoformat()}"
            row, attempt = begin_access(db, kind="medical_access", event_key=event, entity_id=professional_id, email=email)
            if attempt is None:
                return EmailDelivery(row.status)
            delivery = _medical_content(name=name, email=email, temporary_password=temporary_password,
                                        idempotency_key=attempt.idempotency_key)
            finish_access(db, row, attempt, delivery)
            return delivery
    return _medical_content(name=name, email=email, temporary_password=temporary_password,
                            idempotency_key=f"vitta-welcome/{professional_id}/{secrets.token_hex(12)}")


def _medical_content(*, name: str, email: str, temporary_password: str, idempotency_key: str) -> EmailDelivery:
    lines = [f"Olá, {name}.", "Seu acesso ao Vitta-One foi criado.", f"E-mail: {email}",
             f"Senha temporária: {temporary_password}",
             "Esta senha expira em 24 horas. No primeiro acesso será obrigatório escolher uma senha definitiva.",
             "Se você não solicitou esse acesso, avise a administração da clínica."]
    html, text = layout("Seu acesso ao Vitta-One", lines)
    return send(email=email, subject="Seu acesso ao Vitta-One", html=html, text=text,
                idempotency_key=idempotency_key)


def send_patient_portal_invitation(*, name: str, email: str, code: str, activation_url: str, invitation_id: int, idempotency_key: str | None = None) -> EmailDelivery:
    parsed = urlparse(str(activation_url or ""))
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not parsed.netloc or parsed.username or parsed.password or not (parsed.scheme == "https" or local_http):
        return EmailDelivery("NOT_CONFIGURED")
    html, text = layout("Ative seu acesso ao Vitta-One", [f"Olá, {name}.",
        "A Recepção solicitou a ativação do seu acesso ao portal Vitta-One.", f"Código de ativação: {code}",
        "O código é de uso único e expira em 24 horas. Se você não solicitou este acesso, ignore esta mensagem."],
        url=activation_url, link_label="Abrir página de ativação")
    return send(email=email, subject="Ative seu acesso ao Vitta-One", html=html, text=text,
                idempotency_key=idempotency_key or f"vitta-patient-invite/{invitation_id}/{secrets.token_hex(12)}")
