"""Explicit consent controls, separate from the activation invitation consent."""
from typing import Any
import reflex as rx
from sqlmodel import select

from vitta_one.auth.state import AuthState
from vitta_one.auth.authorization import require_authenticated
from vitta_one.auth.roles import Role
from vitta_one.models.patient_queue import Patient
from vitta_one.models.notification import NotificationPreference
from .service import set_preferences


class NotificationState(rx.State):
    pref_patient_id: int = 0
    agenda: bool = False
    financial: bool = False
    ready: bool = False
    feedback: str = ""

    def _clear(self):
        self.pref_patient_id, self.agenda, self.financial, self.ready, self.feedback = 0, False, False, False, ""

    async def _token(self):
        return (await self.get_state(AuthState)).session_token

    @rx.event
    async def load(self, pref_patient_id: int = 0):
        self._clear()
        try:
            with rx.session() as db:
                identity = require_authenticated(db, await self._token())
                if identity.must_change_password or identity.role not in {Role.PACIENTE, Role.RECEPCIONISTA}:
                    raise PermissionError
                if identity.role == Role.PACIENTE:
                    patient = db.exec(select(Patient).where(Patient.user_id == identity.id)).first()
                else:
                    patient = db.get(Patient, pref_patient_id)
                if patient is None:
                    raise ValueError("Paciente indisponível para comunicação.")
                pref = db.exec(select(NotificationPreference).where(NotificationPreference.patient_id == patient.id)).first()
                self.pref_patient_id = patient.id
                self.agenda = bool(pref and pref.agenda_enabled)
                self.financial = bool(pref and pref.financial_enabled)
                self.ready = True
        except Exception:
            self.feedback = "Não foi possível consultar as preferências. Verifique seu acesso."

    @rx.event
    async def save(self, data: dict[str, Any]):
        try:
            with rx.session() as db:
                set_preferences(db, token=await self._token(), patient_id=self.pref_patient_id,
                                agenda=str(data.get("agenda", "")).casefold() in {"on", "true", "1", "yes"}, financial=str(data.get("financial", "")).casefold() in {"on", "true", "1", "yes"},
                                confirmed=str(data.get("confirmed", "")).casefold() in {"on", "true", "1", "yes"})
            self.agenda, self.financial = str(data.get("agenda", "")).casefold() in {"on", "true", "1", "yes"}, str(data.get("financial", "")).casefold() in {"on", "true", "1", "yes"}
            self.feedback = "Preferências de comunicação salvas. Você pode revogá-las a qualquer momento."
        except (ValueError, PermissionError) as exc:
            if isinstance(exc, PermissionError):
                self._clear()
            self.feedback = str(exc)
        except Exception:
            self.feedback = "Não foi possível salvar. Tente novamente."


def preference_panel(patient_id=0):
    return rx.vstack(
        rx.heading("Comunicações por e-mail", size="3"),
        rx.text("Escolha quais mensagens deseja receber. Esta escolha é independente do convite de acesso ao portal.", size="2"),
        rx.button("Consultar preferências", on_click=NotificationState.load(patient_id), variant="outline"),
        rx.cond(NotificationState.ready & ((patient_id == 0) | (NotificationState.pref_patient_id == patient_id)),
            rx.form(rx.vstack(
                rx.checkbox("Confirmação, alterações e lembrete de consulta", name="agenda", default_checked=NotificationState.agenda),
                rx.checkbox("Cobrança disponível e pagamento recebido", name="financial", default_checked=NotificationState.financial),
                rx.checkbox("Confirmo que estas são as escolhas expressas do paciente", name="confirmed", required=True),
                rx.button("Salvar escolhas", type="submit"), align="start", spacing="3"), on_submit=NotificationState.save, key=NotificationState.pref_patient_id.to_string())),
        rx.cond(NotificationState.feedback != "", rx.text(NotificationState.feedback, role="status", size="2")),
        spacing="3", align="stretch", width="100%",
    )
