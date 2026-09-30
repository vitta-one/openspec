"""Read-only projections used by the explicit local Administrator QA preview."""

from typing import TypedDict

import reflex as rx
from sqlmodel import select

from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    RoleForbiddenError,
    require_role,
)
from vitta_one.auth.roles import Role
from vitta_one.auth.settings import local_admin_preview_enabled
from vitta_one.auth.state import AuthState
from vitta_one.models import Patient, Professional, QueueEntry, Specialty


class PreviewPatientRow(TypedDict):
    id: int
    name: str
    cpf_masked: str


class PreviewQueueRow(TypedDict):
    id: int
    patient_id: int
    patient_name: str
    symptoms: str
    priority: str
    priority_label: str
    status: str
    status_label: str
    entered_at: str


class PreviewProfessionalRow(TypedDict):
    id: int
    name: str
    registration_identifier: str
    is_active: bool
    status_label: str


_PRIORITY_LABELS = {
    "VERMELHO": "Vermelho",
    "AMARELO": "Amarelo",
    "VERDE": "Verde",
}

_QUEUE_STATUS_LABELS = {
    "AGUARDANDO": "Aguardando",
    "EM_ATENDIMENTO": "Em atendimento",
    "FINALIZADO": "Finalizado",
    "RETIRADO": "Retirado",
}


def _mask_cpf(cpf: str) -> str:
    digits = "".join(char for char in cpf if char.isdigit())
    suffix = digits[-2:] if len(digits) >= 2 else "**"
    return f"***.***.***-{suffix}"


class AdminPreviewState(rx.State):
    """Server-authorized, read-only data for local visual QA as Administrator."""

    patients: list[PreviewPatientRow] = []
    queue_rows: list[PreviewQueueRow] = []
    professionals: list[PreviewProfessionalRow] = []
    specialty_count: int = 0

    patient_query: str = ""
    selected_patient_id: int = 0
    selected_patient_name: str = ""
    selected_patient_cpf: str = ""

    is_loading: bool = False
    error_message: str = ""

    waiting_count: int = 0
    attending_count: int = 0
    finalized_count: int = 0
    withdrawn_count: int = 0

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear(self) -> None:
        self.patients = []
        self.queue_rows = []
        self.professionals = []
        self.specialty_count = 0
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self.selected_patient_cpf = ""
        self.waiting_count = 0
        self.attending_count = 0
        self.finalized_count = 0
        self.withdrawn_count = 0

    @rx.var
    def filtered_patients(self) -> list[PreviewPatientRow]:
        query = self.patient_query.strip().casefold()
        if not query:
            return self.patients
        return [
            row
            for row in self.patients
            if query in row["name"].casefold() or query in row["cpf_masked"].casefold()
        ]

    @rx.var
    def selected_patient_history(self) -> list[PreviewQueueRow]:
        if not self.selected_patient_id:
            return []
        return [
            row
            for row in self.queue_rows
            if row["patient_id"] == self.selected_patient_id
        ]

    @rx.var
    def active_clinical_rows(self) -> list[PreviewQueueRow]:
        return [
            row for row in self.queue_rows if row["status"] == "EM_ATENDIMENTO"
        ]

    @rx.event
    def update_patient_query(self, value: str) -> None:
        self.patient_query = value

    @rx.event
    def clear_patient_query(self) -> None:
        self.patient_query = ""

    @rx.event
    def select_patient(self, patient_id: int, name: str, cpf_masked: str) -> None:
        self.selected_patient_id = patient_id
        self.selected_patient_name = name
        self.selected_patient_cpf = cpf_masked

    @rx.event
    async def load(self):
        """Load only persisted data after both local-mode and Administrator checks."""
        self.is_loading = True
        self.error_message = ""
        yield

        if not local_admin_preview_enabled():
            self._clear()
            self.is_loading = False
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
            return

        try:
            token = await self._token()
            with rx.session() as db:
                require_role(db, token, Role.ADMINISTRADOR)

                patient_items = list(
                    db.exec(select(Patient).order_by(Patient.name)).all()
                )
                queue_items = list(
                    db.exec(
                        select(QueueEntry).order_by(QueueEntry.entered_at.desc())
                    ).all()
                )
                professional_items = list(
                    db.exec(select(Professional).order_by(Professional.name)).all()
                )
                specialty_items = list(db.exec(select(Specialty)).all())

                patient_by_id = {
                    item.id: item for item in patient_items if item.id is not None
                }

            self.patients = [
                {
                    "id": item.id or 0,
                    "name": item.name,
                    "cpf_masked": _mask_cpf(item.cpf),
                }
                for item in patient_items
                if item.id is not None
            ]

            self.queue_rows = [
                {
                    "id": item.id or 0,
                    "patient_id": item.patient_id,
                    "patient_name": (
                        patient_by_id[item.patient_id].name
                        if item.patient_id in patient_by_id
                        else "Paciente indisponível"
                    ),
                    "symptoms": item.symptoms,
                    "priority": item.priority,
                    "priority_label": _PRIORITY_LABELS.get(
                        item.priority, item.priority.title()
                    ),
                    "status": item.status,
                    "status_label": _QUEUE_STATUS_LABELS.get(
                        item.status, item.status.title()
                    ),
                    "entered_at": item.entered_at.strftime(
                        "%d/%m/%Y · %H:%M UTC"
                    ),
                }
                for item in queue_items
                if item.id is not None
            ]

            self.professionals = [
                {
                    "id": item.id or 0,
                    "name": item.name,
                    "registration_identifier": item.registration_identifier,
                    "is_active": item.is_active,
                    "status_label": "Ativo" if item.is_active else "Inativo",
                }
                for item in professional_items
                if item.id is not None
            ]
            self.specialty_count = len(specialty_items)

            self.waiting_count = sum(
                1 for row in self.queue_rows if row["status"] == "AGUARDANDO"
            )
            self.attending_count = sum(
                1 for row in self.queue_rows if row["status"] == "EM_ATENDIMENTO"
            )
            self.finalized_count = sum(
                1 for row in self.queue_rows if row["status"] == "FINALIZADO"
            )
            self.withdrawn_count = sum(
                1 for row in self.queue_rows if row["status"] == "RETIRADO"
            )

            if (
                self.selected_patient_id
                and not any(
                    row["id"] == self.selected_patient_id for row in self.patients
                )
            ):
                self.selected_patient_id = 0
                self.selected_patient_name = ""
                self.selected_patient_cpf = ""

        except (AuthenticationRequiredError, RoleForbiddenError):
            self._clear()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear()
            self.error_message = (
                "Não foi possível carregar a visualização local agora. "
                "Atualize a página e tente novamente."
            )
        finally:
            self.is_loading = False
            yield
