"""Authorized operational view and explicit resend; no message content exposed."""
from typing import Any
import reflex as rx
from sqlmodel import select

from vitta_one.auth.state import AuthState
from vitta_one.auth.roles import Role
from vitta_one.auth.authorization import require_authenticated
from vitta_one.models.notification import EmailNotification
from .service import manual_retry

KINDS = {"charge_available": "Cobrança disponível", "payment_received": "Pagamento confirmado",
         "booking_confirmed": "Reserva de consulta", "booking_rescheduled": "Reagendamento",
         "booking_cancelled": "Cancelamento", "booking_reminder": "Lembrete",
         "medical_access": "Acesso médico", "patient_access": "Ativação de paciente"}
STATUS = {"PENDING": "Solicitado", "SENDING": "Em processamento", "ACCEPTED": "Aceito pelo provedor",
          "DELIVERED": "Entrega confirmada pelo provedor", "UNKNOWN": "Resultado desconhecido",
          "FAILED": "Falha", "SUPPRESSED": "Envio suprimido", "NOT_CONFIGURED": "Não configurado"}


class EmailOperationsState(rx.State):
    rows: list[dict[str, str]] = []
    selected_notification: int = 0
    feedback: str = ""
    retry_open: bool = False

    def _clear(self):
        self.rows, self.selected_notification, self.feedback, self.retry_open = [], 0, "", False

    async def _token(self):
        return (await self.get_state(AuthState)).session_token

    @rx.event
    async def load(self):
        self._clear()
        try:
            with rx.session() as db:
                identity = require_authenticated(db, await self._token())
                if identity.must_change_password:
                    raise PermissionError
                if identity.role in {Role.FINANCEIRO, Role.ADMINISTRADOR}:
                    kinds = ["charge_available", "payment_received"]
                elif identity.role == Role.RECEPCIONISTA:
                    kinds = ["booking_confirmed", "booking_rescheduled", "booking_cancelled", "booking_reminder"]
                else:
                    raise PermissionError
                rows = db.exec(select(EmailNotification).where(EmailNotification.kind.in_(kinds)).order_by(EmailNotification.id.desc()).limit(20)).all()
                self.rows = [{"id": str(n.id), "kind": KINDS[n.kind], "status": STATUS.get(n.status, "Revisar"),
                              "created": n.created_at.isoformat()} for n in rows]
        except Exception:
            self.feedback = "Não foi possível consultar as notificações. Verifique seu acesso."

    @rx.event
    def begin_retry(self, notification_id: str):
        self.selected_notification, self.retry_open = int(notification_id), True

    @rx.event
    def close_retry(self, value: bool):
        self.retry_open = value

    @rx.event
    async def retry(self, data: dict[str, Any]):
        try:
            with rx.session() as db:
                manual_retry(db, token=await self._token(), notification_id=self.selected_notification,
                             reason=data.get("reason", ""), uncertainty_reviewed=str(data.get("reviewed", "")).casefold() in {"on", "true", "1", "yes"})
            self.retry_open = False
            await self.load()
            self.feedback = "Solicitação de reenvio registrada para processamento."
        except (ValueError, PermissionError) as exc:
            if isinstance(exc, PermissionError):
                self._clear()
            self.feedback = str(exc)
        except Exception:
            self.feedback = "Não foi possível solicitar reenvio. Consulte a situação antes de repetir."


def operations_panel():
    S = EmailOperationsState
    return rx.vstack(rx.heading("Notificações por e-mail", size="3"),
        rx.text("Aceitação pelo provedor não significa entrega na caixa de entrada. Exibindo até 20 solicitações recentes.", size="2"),
        rx.button("Consultar envios", on_click=S.load, variant="outline"),
        rx.foreach(S.rows, lambda row: rx.flex(rx.text(row["kind"]), rx.text(row["status"]),
            rx.button("Revisar reenvio", on_click=S.begin_retry(row["id"]), variant="outline"), gap="3", flex_wrap="wrap")),
        rx.cond(S.feedback != "", rx.text(S.feedback, role="status")),
        rx.dialog.root(rx.dialog.content(rx.dialog.title("Revisar reenvio"),
            rx.dialog.description("Somente falha ou configuração ausente permite nova tentativa. Para resultado desconhecido, confira primeiro o provedor. Mensagem já aceita não será reenviada."),
            rx.form(rx.vstack(rx.input(name="reason", placeholder="Motivo, sem dados clínicos", required=True, min_length=3, max_length=240, aria_label="Motivo do reenvio"),
                rx.checkbox("Revisei o resultado no provedor e autorizo nova tentativa", name="reviewed"),
                rx.button("Solicitar reenvio", type="submit"), rx.dialog.close(rx.button("Voltar", variant="outline")), spacing="3"), on_submit=S.retry)),
            open=S.retry_open, on_open_change=S.close_retry), spacing="3", align="stretch", width="100%")
