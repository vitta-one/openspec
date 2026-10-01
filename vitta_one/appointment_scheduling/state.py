"""Reflex state for Administrator availability and Reception appointment agenda."""

from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.application import (
    admin_create_availability_slot,
    admin_list_active_professionals,
    admin_list_availability_slots,
    admin_set_availability_slot_active,
    reception_cancel_consultation,
    reception_get_agenda,
    reception_list_active_professionals,
    reception_reschedule_consultation,
    reception_schedule_consultation,
)
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError,
    SchedulingNotFoundError,
    SchedulingTransitionError,
    SchedulingValidationError,
)
from vitta_one.appointment_scheduling.settings import ClinicTimezoneConfigurationError
from vitta_one.appointment_scheduling.temporal import (
    SchedulingTimeValidationError,
    clinic_date_after_iso,
    clinic_today_iso,
    format_clinic_datetime,
)
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.application import reception_find_patient


class ProfessionalOptionRow(TypedDict):
    id: int
    value: str
    label: str


class SlotRow(TypedDict):
    id: int
    professional_id: int
    professional_name: str
    starts_at: str
    status: str
    status_label: str


class ConsultationRow(TypedDict):
    id: int
    patient_id: int
    patient_name: str
    professional_id: int
    professional_name: str
    slot_id: int
    scheduled_at: str
    status: str
    status_label: str


def _professional_rows(items) -> list[ProfessionalOptionRow]:
    return [
        {
            "id": item.id,
            "value": str(item.id),
            "label": f"{item.name} · {item.registration_identifier}",
        }
        for item in items
    ]


def _slot_rows(items) -> list[SlotRow]:
    return [
        {
            "id": item.id,
            "professional_id": item.professional_id,
            "professional_name": item.professional_name,
            "starts_at": format_clinic_datetime(item.starts_at),
            "status": item.status.value,
            "status_label": item.status.label,
        }
        for item in items
    ]


def _consultation_rows(items) -> list[ConsultationRow]:
    return [
        {
            "id": item.id,
            "patient_id": item.patient_id,
            "patient_name": item.patient_name,
            "professional_id": item.professional_id,
            "professional_name": item.professional_name,
            "slot_id": item.availability_slot_id,
            "scheduled_at": format_clinic_datetime(item.scheduled_at),
            "status": item.status.value,
            "status_label": item.status.label,
        }
        for item in items
    ]


class AdminAvailabilityState(rx.State):
    """Administrator-only availability management with server-side RBAC."""

    professionals: list[ProfessionalOptionRow] = []
    slots: list[SlotRow] = []

    selected_professional: str = "__none__"
    slot_datetime_local: str = ""
    filter_professional: str = "__all__"
    filter_start_date: str = ""
    filter_end_date: str = ""

    is_loading: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    @rx.var
    def has_professionals(self) -> bool:
        return bool(self.professionals)

    @rx.var
    def has_slots(self) -> bool:
        return bool(self.slots)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _clear_sensitive(self) -> None:
        self.professionals = []
        self.slots = []
        self.selected_professional = "__none__"

    def _professional_filter_id(self) -> int | None:
        return None if self.filter_professional == "__all__" else int(self.filter_professional)

    def _ensure_default_period(self) -> None:
        if not self.filter_start_date:
            self.filter_start_date = clinic_today_iso()
        if not self.filter_end_date:
            self.filter_end_date = clinic_date_after_iso(14)

    def _load_with_token(self, token: str) -> None:
        self._ensure_default_period()
        with rx.session() as db:
            professional_items = admin_list_active_professionals(db, token=token)
            slot_items = admin_list_availability_slots(
                db,
                token=token,
                professional_id=self._professional_filter_id(),
                start_date=self.filter_start_date,
                end_date=self.filter_end_date,
            )
        self.professionals = _professional_rows(professional_items)
        self.slots = _slot_rows(slot_items)
        if self.selected_professional == "__none__" and self.professionals:
            self.selected_professional = self.professionals[0]["value"]

    async def _authorization_redirect(self, exc: Exception):
        self._clear_sensitive()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    @rx.event
    async def load(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (ClinicTimezoneConfigurationError, SchedulingTimeValidationError) as exc:
            self.error_message = str(exc)
            self.slots = []
        except Exception:
            self.error_message = "Não foi possível carregar a disponibilidade agora."
            self.slots = []
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_selected_professional(self, value: str) -> None:
        self.selected_professional = value

    @rx.event
    def update_slot_datetime(self, value: str) -> None:
        self.slot_datetime_local = value

    @rx.event
    def update_filter_professional(self, value: str) -> None:
        self.filter_professional = value

    @rx.event
    def update_filter_start_date(self, value: str) -> None:
        self.filter_start_date = value

    @rx.event
    def update_filter_end_date(self, value: str) -> None:
        self.filter_end_date = value

    @rx.event
    async def refresh(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (SchedulingTimeValidationError, ClinicTimezoneConfigurationError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível atualizar a disponibilidade agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def create_slot(self, _form_data: dict[str, object]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if self.selected_professional == "__none__":
                raise SchedulingValidationError("Selecione um profissional ativo.")
            token = await self._token()
            with rx.session() as db:
                admin_create_availability_slot(
                    db,
                    token=token,
                    professional_id=int(self.selected_professional),
                    starts_at_local=self.slot_datetime_local,
                )
            self.slot_datetime_local = ""
            self._load_with_token(token)
            self.success_message = "Horário disponibilizado."
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingTimeValidationError,
            ClinicTimezoneConfigurationError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível criar o horário agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def toggle_slot(self, slot_id: int, current_status: str):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if current_status == AvailabilitySlotStatus.BOOKED.value:
                raise SchedulingTransitionError(
                    "Horários reservados precisam ser tratados pela Recepção."
                )
            token = await self._token()
            activate = current_status == AvailabilitySlotStatus.INACTIVE.value
            with rx.session() as db:
                admin_set_availability_slot_active(
                    db,
                    token=token,
                    slot_id=slot_id,
                    is_active=activate,
                )
            self._load_with_token(token)
            self.success_message = "Horário reativado." if activate else "Horário desativado."
        except (
            SchedulingTransitionError,
            SchedulingNotFoundError,
            SchedulingValidationError,
            ClinicTimezoneConfigurationError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível alterar o horário agora."
        finally:
            self.is_submitting = False
            yield


class ReceptionAgendaState(rx.State):
    """Reception-only appointment scheduling state with simple, explicit flows."""

    professionals: list[ProfessionalOptionRow] = []
    slots: list[SlotRow] = []
    consultations: list[ConsultationRow] = []

    filter_professional: str = "__all__"
    filter_start_date: str = ""
    filter_end_date: str = ""

    patient_cpf: str = ""
    selected_patient_id: int = 0
    selected_patient_name: str = ""

    reschedule_dialog_open: bool = False
    reschedule_consultation_id: int = 0
    reschedule_patient_name: str = ""
    selected_new_slot: str = "__none__"

    cancel_dialog_open: bool = False
    cancel_consultation_id: int = 0
    cancel_patient_name: str = ""
    cancel_scheduled_at: str = ""

    is_loading: bool = False
    is_submitting: bool = False
    error_message: str = ""
    success_message: str = ""

    @rx.var
    def available_slots(self) -> list[SlotRow]:
        return [
            row
            for row in self.slots
            if row["status"] == AvailabilitySlotStatus.AVAILABLE.value
        ]

    @rx.var
    def has_available_slots(self) -> bool:
        return any(
            row["status"] == AvailabilitySlotStatus.AVAILABLE.value
            for row in self.slots
        )

    @rx.var
    def has_consultations(self) -> bool:
        return bool(self.consultations)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_feedback(self) -> None:
        self.error_message = ""
        self.success_message = ""

    def _clear_sensitive(self) -> None:
        self.professionals = []
        self.slots = []
        self.consultations = []
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self._reset_reschedule()
        self._reset_cancel()

    def _professional_filter_id(self) -> int | None:
        return None if self.filter_professional == "__all__" else int(self.filter_professional)

    def _ensure_default_period(self) -> None:
        if not self.filter_start_date:
            self.filter_start_date = clinic_today_iso()
        if not self.filter_end_date:
            self.filter_end_date = clinic_date_after_iso(7)

    def _load_with_token(self, token: str) -> None:
        self._ensure_default_period()
        with rx.session() as db:
            professional_items = reception_list_active_professionals(db, token=token)
            snapshot = reception_get_agenda(
                db,
                token=token,
                professional_id=self._professional_filter_id(),
                start_date=self.filter_start_date,
                end_date=self.filter_end_date,
            )
        self.professionals = _professional_rows(professional_items)
        self.slots = _slot_rows(snapshot.slots)
        self.consultations = _consultation_rows(snapshot.consultations)

    def _reset_reschedule(self) -> None:
        self.reschedule_dialog_open = False
        self.reschedule_consultation_id = 0
        self.reschedule_patient_name = ""
        self.selected_new_slot = "__none__"

    def _reset_cancel(self) -> None:
        self.cancel_dialog_open = False
        self.cancel_consultation_id = 0
        self.cancel_patient_name = ""
        self.cancel_scheduled_at = ""

    async def _authorization_redirect(self, exc: Exception):
        self._clear_sensitive()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    @rx.event
    async def load(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (ClinicTimezoneConfigurationError, SchedulingTimeValidationError) as exc:
            self.error_message = str(exc)
        except Exception:
            self.error_message = "Não foi possível carregar a agenda agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_filter_professional(self, value: str) -> None:
        self.filter_professional = value

    @rx.event
    def update_filter_start_date(self, value: str) -> None:
        self.filter_start_date = value

    @rx.event
    def update_filter_end_date(self, value: str) -> None:
        self.filter_end_date = value

    @rx.event
    async def refresh(self):
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (SchedulingTimeValidationError, ClinicTimezoneConfigurationError) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível atualizar a agenda agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_patient_cpf(self, value: str) -> None:
        self.patient_cpf = value

    @rx.event
    async def find_patient(self, _form_data: dict[str, object]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_find_patient(db, token=token, cpf=self.patient_cpf)
            if patient is None or patient.id is None:
                self.selected_patient_id = 0
                self.selected_patient_name = ""
                self.error_message = "Paciente não encontrado. Confira o CPF ou cadastre-o na Recepção."
            else:
                self.selected_patient_id = patient.id
                self.selected_patient_name = patient.name
                self.success_message = "Paciente selecionado para agendamento."
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível localizar o paciente agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def clear_patient(self) -> None:
        self.patient_cpf = ""
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self._clear_feedback()

    @rx.event
    async def schedule(self, slot_id: int):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.selected_patient_id:
                raise SchedulingValidationError(
                    "Localize um paciente antes de escolher o horário."
                )
            token = await self._token()
            with rx.session() as db:
                reception_schedule_consultation(
                    db,
                    token=token,
                    patient_id=self.selected_patient_id,
                    slot_id=slot_id,
                )
            self._load_with_token(token)
            self.success_message = "Consulta agendada."
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingNotFoundError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível agendar a consulta agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_reschedule(self, consultation_id: int, patient_name: str) -> None:
        self._clear_feedback()
        self.reschedule_consultation_id = consultation_id
        self.reschedule_patient_name = patient_name
        self.selected_new_slot = "__none__"
        self.reschedule_dialog_open = True

    @rx.event
    def set_reschedule_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.reschedule_dialog_open = is_open
        if not is_open:
            self._reset_reschedule()

    @rx.event
    def update_new_slot(self, value: str) -> None:
        self.selected_new_slot = value

    @rx.event
    async def confirm_reschedule(self):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.reschedule_consultation_id or self.selected_new_slot == "__none__":
                raise SchedulingValidationError("Selecione o novo horário.")
            token = await self._token()
            with rx.session() as db:
                reception_reschedule_consultation(
                    db,
                    token=token,
                    consultation_id=self.reschedule_consultation_id,
                    new_slot_id=int(self.selected_new_slot),
                )
            self._reset_reschedule()
            self._load_with_token(token)
            self.success_message = "Consulta reagendada."
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingNotFoundError,
            SchedulingTransitionError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível reagendar a consulta agora."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_cancel(
        self,
        consultation_id: int,
        patient_name: str,
        scheduled_at: str,
    ) -> None:
        self._clear_feedback()
        self.cancel_consultation_id = consultation_id
        self.cancel_patient_name = patient_name
        self.cancel_scheduled_at = scheduled_at
        self.cancel_dialog_open = True

    @rx.event
    def set_cancel_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.cancel_dialog_open = is_open
        if not is_open:
            self._reset_cancel()

    @rx.event
    async def confirm_cancel(self):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.cancel_consultation_id:
                raise SchedulingValidationError("Selecione uma consulta agendada.")
            token = await self._token()
            with rx.session() as db:
                reception_cancel_consultation(
                    db,
                    token=token,
                    consultation_id=self.cancel_consultation_id,
                )
            self._reset_cancel()
            self._load_with_token(token)
            self.success_message = "Consulta cancelada; o histórico foi preservado."
        except (
            SchedulingValidationError,
            SchedulingNotFoundError,
            SchedulingTransitionError,
        ) as exc:
            self.error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível cancelar a consulta agora."
        finally:
            self.is_submitting = False
            yield
