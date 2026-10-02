"""Read-only projections used by the explicit local Administrator QA preview."""

from typing import TypedDict

import reflex as rx
from sqlmodel import select

from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    RoleForbiddenError,
)
from vitta_one.auth.roles import Role
from vitta_one.admin_preview.service import (
    LocalAdminPreviewDisabledError,
    require_local_admin_preview,
)
from vitta_one.auth.state import AuthState
from vitta_one.clinical_care.application import admin_preview_patient_history
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.models import (
    ClinicalCareRecord,
    Consultation,
    Patient,
    Professional,
    ProfessionalAvailabilitySlot,
    QueueEntry,
    Specialty,
)


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
    is_scheduled: bool
    has_clinical_record: bool
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str


class PreviewProfessionalRow(TypedDict):
    id: int
    name: str
    registration_identifier: str
    is_active: bool
    status_label: str


class PreviewAgendaSlotRow(TypedDict):
    id: int
    professional_name: str
    starts_at: str
    status: str
    status_label: str


class PreviewConsultationRow(TypedDict):
    id: int
    patient_name: str
    professional_name: str
    scheduled_at: str
    status: str
    status_label: str
    confirmed_at: str
    started_at: str
    completed_at: str
    cancelled_at: str


class PreviewClinicalHistoryRow(TypedDict):
    record_id: int
    consultation_id: int
    professional_name: str
    scheduled_at: str
    completed_at: str
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str


def _serialize_clinical_history_item(item) -> PreviewClinicalHistoryRow:
    return {
        "record_id": item.record_id,
        "consultation_id": item.consultation_id,
        "professional_name": item.professional_name,
        "scheduled_at": format_clinic_datetime(item.scheduled_at),
        "completed_at": format_clinic_datetime(item.completed_at),
        "chief_complaint": item.chief_complaint,
        "anamnesis": item.anamnesis,
        "diagnosis": item.diagnosis,
        "conduct_notes": item.conduct_notes,
    }


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

PATIENT_PAGE_SIZE = 8


def _mask_cpf(cpf: str) -> str:
    digits = "".join(char for char in cpf if char.isdigit())
    suffix = digits[-2:] if len(digits) >= 2 else "**"
    return f"***.***.***-{suffix}"


def _filter_patient_rows(
    patients: list[PreviewPatientRow],
    query: str,
) -> list[PreviewPatientRow]:
    normalized = query.strip().casefold()
    if not normalized:
        return patients
    return [
        row
        for row in patients
        if normalized in row["name"].casefold()
        or normalized in row["cpf_masked"].casefold()
    ]


def _patient_page_count(total: int, page_size: int = PATIENT_PAGE_SIZE) -> int:
    if page_size <= 0:
        raise ValueError("O tamanho da página deve ser positivo.")
    return max(1, (total + page_size - 1) // page_size)


def _patient_page_rows(
    patients: list[PreviewPatientRow],
    query: str,
    page: int,
    page_size: int = PATIENT_PAGE_SIZE,
) -> list[PreviewPatientRow]:
    filtered = _filter_patient_rows(patients, query)
    safe_page = min(max(page, 1), _patient_page_count(len(filtered), page_size))
    start = (safe_page - 1) * page_size
    return filtered[start : start + page_size]


class AdminPreviewState(rx.State):
    """Server-authorized, read-only data for local visual QA as Administrator."""

    patients: list[PreviewPatientRow] = []
    queue_rows: list[PreviewQueueRow] = []
    professionals: list[PreviewProfessionalRow] = []
    specialty_count: int = 0
    agenda_slots: list[PreviewAgendaSlotRow] = []
    agenda_consultations: list[PreviewConsultationRow] = []

    patient_query: str = ""
    patient_page: int = 1
    patient_page_size: int = PATIENT_PAGE_SIZE
    selected_patient_id: int = 0
    selected_patient_name: str = ""
    selected_patient_cpf: str = ""
    selected_clinical_history: list[PreviewClinicalHistoryRow] = []
    clinical_history_page: int = 1
    clinical_history_total_pages: int = 1
    clinical_history_total_count: int = 0

    is_loading: bool = False
    is_loading_clinical_history: bool = False
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
        self.agenda_slots = []
        self.agenda_consultations = []
        self.patient_query = ""
        self.patient_page = 1
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self.selected_patient_cpf = ""
        self.selected_clinical_history = []
        self.clinical_history_page = 1
        self.clinical_history_total_pages = 1
        self.clinical_history_total_count = 0
        self.waiting_count = 0
        self.attending_count = 0
        self.finalized_count = 0
        self.withdrawn_count = 0

    @rx.var
    def filtered_patients(self) -> list[PreviewPatientRow]:
        return _filter_patient_rows(self.patients, self.patient_query)

    @rx.var
    def patient_result_count(self) -> int:
        return len(_filter_patient_rows(self.patients, self.patient_query))

    @rx.var
    def patient_total_pages(self) -> int:
        return _patient_page_count(
            len(_filter_patient_rows(self.patients, self.patient_query)),
            self.patient_page_size,
        )

    @rx.var
    def paginated_patients(self) -> list[PreviewPatientRow]:
        return _patient_page_rows(
            self.patients,
            self.patient_query,
            self.patient_page,
            self.patient_page_size,
        )

    @rx.var
    def patient_range_label(self) -> str:
        total = len(_filter_patient_rows(self.patients, self.patient_query))
        if total == 0:
            return "0 pacientes"
        start = (self.patient_page - 1) * self.patient_page_size + 1
        end = min(self.patient_page * self.patient_page_size, total)
        return f"{start}–{end} de {total} pacientes"

    @rx.var
    def can_previous_patient_page(self) -> bool:
        return self.patient_page > 1

    @rx.var
    def can_next_patient_page(self) -> bool:
        return self.patient_page < _patient_page_count(
            len(_filter_patient_rows(self.patients, self.patient_query)),
            self.patient_page_size,
        )

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

    @rx.var
    def can_previous_clinical_history_page(self) -> bool:
        return self.clinical_history_page > 1

    @rx.var
    def can_next_clinical_history_page(self) -> bool:
        return self.clinical_history_page < self.clinical_history_total_pages

    def _clear_clinical_history(self) -> None:
        self.selected_clinical_history = []
        self.clinical_history_page = 1
        self.clinical_history_total_pages = 1
        self.clinical_history_total_count = 0

    def _clear_patient_selection(self) -> None:
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self.selected_patient_cpf = ""
        self._clear_clinical_history()

    def _load_selected_clinical_history_with_token(
        self,
        token: str,
        *,
        page: int,
    ) -> None:
        if not self.selected_patient_id:
            self._clear_clinical_history()
            return
        with rx.session() as db:
            history = admin_preview_patient_history(
                db,
                token=token,
                patient_id=self.selected_patient_id,
                page=page,
            )
        self.selected_clinical_history = [
            _serialize_clinical_history_item(item) for item in history.items
        ]
        self.clinical_history_page = history.page
        self.clinical_history_total_pages = history.total_pages
        self.clinical_history_total_count = history.total_count

    @rx.event
    def update_patient_query(self, value: str) -> None:
        self.patient_query = value
        self.patient_page = 1
        self._clear_patient_selection()

    @rx.event
    def clear_patient_query(self) -> None:
        self.patient_query = ""
        self.patient_page = 1
        self._clear_patient_selection()

    @rx.event
    async def toggle_patient_selection(
        self,
        patient_id: int,
        name: str,
        cpf_masked: str,
        checked: bool,
    ):
        self.error_message = ""
        if not checked:
            if self.selected_patient_id == patient_id:
                self._clear_patient_selection()
            return

        self.selected_patient_id = patient_id
        self.selected_patient_name = name
        self.selected_patient_cpf = cpf_masked
        self.is_loading_clinical_history = True
        self._clear_clinical_history()
        yield
        try:
            token = await self._token()
            self._load_selected_clinical_history_with_token(token, page=1)
        except LocalAdminPreviewDisabledError:
            self._clear_patient_selection()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except AuthenticationRequiredError:
            self._clear_patient_selection()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_patient_selection()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear_clinical_history()
            self.error_message = (
                "Não foi possível carregar o histórico clínico deste paciente agora."
            )
        finally:
            self.is_loading_clinical_history = False
            yield

    @rx.event
    def clear_patient_selection(self) -> None:
        self._clear_patient_selection()

    @rx.event
    def previous_patient_page(self) -> None:
        if self.patient_page > 1:
            self.patient_page -= 1
            self._clear_patient_selection()

    @rx.event
    def next_patient_page(self) -> None:
        total_pages = _patient_page_count(
            len(_filter_patient_rows(self.patients, self.patient_query)),
            self.patient_page_size,
        )
        if self.patient_page < total_pages:
            self.patient_page += 1
            self._clear_patient_selection()

    @rx.event
    async def previous_clinical_history_page(self):
        if not self.selected_patient_id or self.clinical_history_page <= 1:
            return
        self.is_loading_clinical_history = True
        yield
        try:
            token = await self._token()
            self._load_selected_clinical_history_with_token(
                token,
                page=self.clinical_history_page - 1,
            )
        except LocalAdminPreviewDisabledError:
            self._clear_patient_selection()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except AuthenticationRequiredError:
            self._clear_patient_selection()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_patient_selection()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível atualizar o histórico clínico agora."
        finally:
            self.is_loading_clinical_history = False
            yield

    @rx.event
    async def next_clinical_history_page(self):
        if (
            not self.selected_patient_id
            or self.clinical_history_page >= self.clinical_history_total_pages
        ):
            return
        self.is_loading_clinical_history = True
        yield
        try:
            token = await self._token()
            self._load_selected_clinical_history_with_token(
                token,
                page=self.clinical_history_page + 1,
            )
        except LocalAdminPreviewDisabledError:
            self._clear_patient_selection()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except AuthenticationRequiredError:
            self._clear_patient_selection()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_patient_selection()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível atualizar o histórico clínico agora."
        finally:
            self.is_loading_clinical_history = False
            yield

    @rx.event
    async def load(self):
        """Load only persisted data after both local-mode and Administrator checks."""
        self.is_loading = True
        self.error_message = ""
        yield

        try:
            token = await self._token()
            with rx.session() as db:
                require_local_admin_preview(db, token)

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
                slot_items = list(
                    db.exec(
                        select(ProfessionalAvailabilitySlot)
                        .order_by(ProfessionalAvailabilitySlot.starts_at)
                        .limit(80)
                    ).all()
                )
                consultation_items = list(
                    db.exec(
                        select(Consultation)
                        .order_by(Consultation.scheduled_at)
                        .limit(80)
                    ).all()
                )
                clinical_items = list(
                    db.exec(
                        select(ClinicalCareRecord)
                        .order_by(ClinicalCareRecord.updated_at.desc())
                        .limit(120)
                    ).all()
                )

                patient_by_id = {
                    item.id: item for item in patient_items if item.id is not None
                }
                professional_by_id = {
                    item.id: item for item in professional_items if item.id is not None
                }
                clinical_by_consultation_id = {
                    item.consultation_id: item
                    for item in clinical_items
                    if item.id is not None
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
                    "is_scheduled": item.consultation_id is not None,
                    "has_clinical_record": (
                        item.consultation_id in clinical_by_consultation_id
                        if item.consultation_id is not None
                        else False
                    ),
                    "chief_complaint": (
                        clinical_by_consultation_id[item.consultation_id].chief_complaint
                        if item.consultation_id in clinical_by_consultation_id
                        else ""
                    ),
                    "anamnesis": (
                        clinical_by_consultation_id[item.consultation_id].anamnesis
                        if item.consultation_id in clinical_by_consultation_id
                        else ""
                    ),
                    "diagnosis": (
                        clinical_by_consultation_id[item.consultation_id].diagnosis
                        if item.consultation_id in clinical_by_consultation_id
                        else ""
                    ),
                    "conduct_notes": (
                        clinical_by_consultation_id[item.consultation_id].conduct_notes
                        if item.consultation_id in clinical_by_consultation_id
                        else ""
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

            self.agenda_slots = [
                {
                    "id": item.id or 0,
                    "professional_name": (
                        professional_by_id[item.professional_id].name
                        if item.professional_id in professional_by_id
                        else "Profissional indisponível"
                    ),
                    "starts_at": format_clinic_datetime(item.starts_at),
                    "status": item.status,
                    "status_label": AvailabilitySlotStatus(item.status).label,
                }
                for item in slot_items
                if item.id is not None
            ]
            self.agenda_consultations = [
                {
                    "id": item.id or 0,
                    "patient_name": (
                        patient_by_id[item.patient_id].name
                        if item.patient_id in patient_by_id
                        else "Paciente indisponível"
                    ),
                    "professional_name": (
                        professional_by_id[item.professional_id].name
                        if item.professional_id in professional_by_id
                        else "Profissional indisponível"
                    ),
                    "scheduled_at": format_clinic_datetime(item.scheduled_at),
                    "status": item.status,
                    "status_label": ConsultationStatus(item.status).label,
                    "confirmed_at": (
                        format_clinic_datetime(item.confirmed_at)
                        if item.confirmed_at is not None
                        else ""
                    ),
                    "started_at": (
                        format_clinic_datetime(item.started_at)
                        if item.started_at is not None
                        else ""
                    ),
                    "completed_at": (
                        format_clinic_datetime(item.completed_at)
                        if item.completed_at is not None
                        else ""
                    ),
                    "cancelled_at": (
                        format_clinic_datetime(item.cancelled_at)
                        if item.cancelled_at is not None
                        else ""
                    ),
                }
                for item in consultation_items
                if item.id is not None
            ]

            total_pages = _patient_page_count(
                len(_filter_patient_rows(self.patients, self.patient_query)),
                self.patient_page_size,
            )
            self.patient_page = min(max(self.patient_page, 1), total_pages)

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
                self._clear_patient_selection()
            elif self.selected_patient_id:
                self._load_selected_clinical_history_with_token(
                    token,
                    page=self.clinical_history_page,
                )

        except LocalAdminPreviewDisabledError:
            self._clear()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except AuthenticationRequiredError:
            self._clear()
            yield rx.redirect("/login")
        except RoleForbiddenError:
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
