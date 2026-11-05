"""Reflex state for Administrator availability and Reception appointment agenda."""

from typing import Any, TypedDict
import calendar
from datetime import date, datetime, timedelta, timezone

import reflex as rx

from vitta_one.appointment_scheduling.application import (
    admin_create_availability_slot,
    admin_get_weekly_schedule,
    admin_save_weekly_schedule,
    admin_list_active_professionals,
    admin_list_availability_slots,
    admin_set_availability_slot_active,
    reception_cancel_consultation,
    reception_get_agenda,
    reception_get_consultation_by_id,
    reception_list_active_professionals,
    reception_list_booking_professionals,
    reception_reschedule_consultation,
    reception_schedule_consultation,
)
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.ical_export import build_consultation_ics
from vitta_one.appointment_scheduling.reception_calendar import (
    AgendaWeekDay,
    build_week_days,
    filter_consultations_for_day,
    week_bounds,
)
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
from vitta_one.consultation_care.application import reception_confirm_arrival
from vitta_one.consultation_care.service import (
    CareLifecycleConflictError,
    CareLifecycleTransitionError,
    CareLifecycleValidationError,
)
from vitta_one.patient_queue.application import (
    reception_find_patient,
    reception_get_patient_identity,
    reception_search_patients,
)
from vitta_one.patient_queue.state import ReceptionQueueState


class ProfessionalOptionRow(TypedDict):
    id: int
    value: str
    label: str


class SlotRow(TypedDict):
    id: int
    value: str
    professional_id: int
    professional_name: str
    starts_at: str
    date_label: str
    time_label: str
    status: str
    status_label: str



class SlotDayGroup(TypedDict):
    date_label: str
    slots: list[SlotRow]


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
    """Present readable names; technical INT registrations stay out of the UI."""
    rows = list(items)
    duplicates: dict[str, int] = {}
    for item in rows:
        duplicates[item.name] = duplicates.get(item.name, 0) + 1

    result: list[ProfessionalOptionRow] = []
    for item in rows:
        label = item.name
        if duplicates[item.name] > 1:
            registration = (item.registration_identifier or "").strip()
            if registration and not registration.upper().startswith("INT-"):
                label = f"{item.name} · {registration}"
            else:
                label = f"{item.name} · cadastro {item.id}"
        result.append({"id": item.id, "value": str(item.id), "label": label})
    return result


def _slot_rows(items) -> list[SlotRow]:
    return [
        {
            "id": item.id,
            "value": str(item.id),
            "professional_id": item.professional_id,
            "professional_name": item.professional_name,
            "starts_at": format_clinic_datetime(item.starts_at),
            "date_label": format_clinic_datetime(item.starts_at).split(" às ")[0],
            "time_label": format_clinic_datetime(item.starts_at).split(" às ")[1],
            "status": item.status.value,
            "status_label": item.status.label,
        }
        for item in items
    ]


def group_slots_by_day(slots: list[SlotRow]) -> list[SlotDayGroup]:
    """Group already chronologically sorted persisted slots without changing data."""
    by_date: dict[str, list[SlotRow]] = {}
    for slot in slots:
        by_date.setdefault(slot["date_label"], []).append(slot)
    return [
        {"date_label": date_label, "slots": items}
        for date_label, items in by_date.items()
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


class AdminCalendarCell(TypedDict):
    date_label: str
    day: str
    is_current_month: bool
    is_selected: bool
    has_slots: bool
    slot_count: int
    aria_label: str


def build_admin_calendar_cells(
    slots: list[SlotRow], month_value: str, selected: str,
) -> list[AdminCalendarCell]:
    """Build a calendar from persisted data, without fabricating availability."""
    try:
        year, month = map(int, month_value.split("-"))
        date(year, month, 1)
    except (ValueError, IndexError):
        return []
    by_day: dict[str, int] = {}
    for slot in slots:
        label = slot["date_label"]
        by_day[label] = by_day.get(label, 0) + 1
    days: list[AdminCalendarCell] = []
    for day in calendar.Calendar(firstweekday=6).itermonthdates(year, month):
        label = day.strftime("%d/%m/%Y")
        count = by_day.get(label, 0)
        days.append({
            "date_label": label,
            "day": str(day.day),
            "is_current_month": day.month == month,
            "is_selected": label == selected,
            "has_slots": count > 0 and day.month == month,
            "slot_count": count if day.month == month else 0,
            "aria_label": f"{label}: {count} horário(s) configurado(s)" if count and day.month == month else f"{label}: sem horários",
        })
    return days


class BookingProfessionalRow(TypedDict):
    id: int
    value: str
    label: str
    specialties: str


class BookingPatientRow(TypedDict):
    id: int
    name: str
    contact_hint: str


def _masked_booking_contact(value: str | None) -> str:
    digits = "".join(char for char in (value or "") if char.isdigit())
    return f"Telefone final {digits[-4:]}" if len(digits) >= 4 else "Telefone não informado"


def booking_calendar_cells(
    slots: list[SlotRow],
    month_label: str,
    selected_date: str,
    today_iso: str,
    end_iso: str,
) -> list[AdminCalendarCell]:
    """An accessible month built only from genuinely bookable persisted slots."""
    try:
        year, month = map(int, month_label.split("-"))
        start = date.fromisoformat(today_iso)
        end = date.fromisoformat(end_iso)
        date(year, month, 1)
    except (ValueError, IndexError):
        return []
    counts: dict[str, int] = {}
    for slot in slots:
        if slot["status"] == AvailabilitySlotStatus.AVAILABLE.value:
            counts[slot["date_label"]] = counts.get(slot["date_label"], 0) + 1
    cells: list[AdminCalendarCell] = []
    for day in calendar.Calendar(firstweekday=6).itermonthdates(year, month):
        label = day.strftime("%d/%m/%Y")
        count = counts.get(label, 0) if start <= day <= end and day.month == month else 0
        cells.append({
            "date_label": label,
            "day": str(day.day),
            "is_current_month": day.month == month,
            "is_selected": label == selected_date,
            "has_slots": count > 0,
            "slot_count": count,
            "aria_label": f"{label}: {count} horário(s) disponível(is)" if count else f"{label}: sem horários disponíveis",
        })
    return cells


class AdminAvailabilityState(rx.State):
    """Administrator-only availability management with server-side RBAC."""

    professionals: list[ProfessionalOptionRow] = []
    slots: list[SlotRow] = []

    selected_professional: str = "__none__"
    weekly_start_day: str = "0"
    weekly_end_day: str = "4"
    weekly_start_time: str = "08:00"
    weekly_end_time: str = "17:00"
    weekly_slot_minutes: str = "30"
    weekly_existing: bool = False
    weekly_saved_summary: str = ""
    slot_datetime_local: str = ""
    slot_date_local: str = ""
    slot_time_local: str = ""
    filter_professional: str = "__all__"
    filter_start_date: str = ""
    filter_end_date: str = ""
    calendar_month: str = ""
    selected_calendar_day: str = ""
    active_operation: str = "search"

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

    @rx.var
    def slots_by_day(self) -> list[SlotDayGroup]:
        return group_slots_by_day(self.slots)

    @rx.var
    def calendar_month_title(self) -> str:
        """Mês visível da clínica, sem depender do idioma do sistema."""
        try:
            year, month = map(int, self.calendar_month.split("-"))
            return f"{('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro')[month - 1]} {year}"
        except (ValueError, IndexError):
            return ""

    @rx.var
    def calendar_days(self) -> list[AdminCalendarCell]:
        return build_admin_calendar_cells(
            self.slots, self.calendar_month, self.selected_calendar_day
        )

    @rx.var
    def selected_day_slots(self) -> list[SlotRow]:
        return [slot for slot in self.slots if slot["date_label"] == self.selected_calendar_day]

    @rx.var
    def selected_day_available(self) -> int:
        return sum(slot["status"] == AvailabilitySlotStatus.AVAILABLE.value for slot in self.selected_day_slots)

    @rx.var
    def selected_day_booked(self) -> int:
        return sum(slot["status"] == AvailabilitySlotStatus.BOOKED.value for slot in self.selected_day_slots)

    @rx.var
    def selected_day_inactive(self) -> int:
        return sum(slot["status"] == AvailabilitySlotStatus.INACTIVE.value for slot in self.selected_day_slots)

    @rx.event
    def select_calendar_day(self, label: str) -> None:
        """Allow inspection of an empty date, never of a different visible month."""
        try:
            selected = datetime.strptime(label, "%d/%m/%Y").date()
        except ValueError:
            return
        if selected.strftime("%Y-%m") == self.calendar_month:
            self.selected_calendar_day = label

    @rx.event
    def change_operation(self, value: str) -> None:
        if value in ("search", "weekly", "single"):
            self.active_operation = value

    @rx.event
    async def move_calendar_month(self, delta: int):
        if delta not in (-1, 1):
            return
        try:
            year, month = map(int, self.calendar_month.split("-"))
            ordinal = year * 12 + month - 1 + delta
            new_year, month_index = divmod(ordinal, 12)
            if new_year < 2000 or new_year > 2100:
                return
            month = month_index + 1
            self.calendar_month = f"{new_year:04d}-{month:02d}"
            self.filter_start_date = f"{new_year:04d}-{month:02d}-01"
            self.filter_end_date = f"{new_year:04d}-{month:02d}-{calendar.monthrange(new_year, month)[1]:02d}"
            self.selected_calendar_day = ""
            self.is_loading = True
            yield
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            yield rx.toast.error("Não foi possível carregar os horários do mês.", position="top-right")
        finally:
            self.is_loading = False
            yield

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
        self.selected_calendar_day = ""

    def _apply_weekly_rule(self, rule) -> None:
        self.weekly_existing = rule is not None
        self.weekly_start_day = str(rule.weekday_start) if rule is not None else "0"
        self.weekly_end_day = str(rule.weekday_end) if rule is not None else "4"
        self.weekly_start_time = rule.time_start if rule is not None else "08:00"
        self.weekly_end_time = rule.time_end if rule is not None else "17:00"
        self.weekly_slot_minutes = str(rule.slot_minutes) if rule is not None else "30"
        if rule is None:
            self.weekly_saved_summary = ""
        else:
            weekdays = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
            day_label = weekdays[rule.weekday_start]
            if rule.weekday_end != rule.weekday_start:
                day_label += f"–{weekdays[rule.weekday_end]}"
            self.weekly_saved_summary = (
                f"{day_label} · {rule.time_start}–{rule.time_end} · "
                f"{rule.slot_minutes} minutos por consulta"
            )

    def _professional_filter_id(self) -> int | None:
        return None if self.filter_professional == "__all__" else int(self.filter_professional)

    def _ensure_default_period(self) -> None:
        if not self.calendar_month:
            self.calendar_month = clinic_today_iso()[:7]
        if not self.filter_start_date or not self.filter_end_date:
            year, month = map(int, self.calendar_month.split("-"))
            self.filter_start_date = f"{year:04d}-{month:02d}-01"
            self.filter_end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"

    def _load_with_token(self, token: str) -> None:
        self._ensure_default_period()
        with rx.session() as db:
            professional_items = admin_list_active_professionals(db, token=token)
            professionals = _professional_rows(professional_items)
            allowed = {item["value"] for item in professionals}
            if self.selected_professional not in allowed:
                self.selected_professional = professionals[0]["value"] if professionals else "__none__"
            self.filter_professional = (
                self.selected_professional if self.selected_professional != "__none__" else "__all__"
            )
            slot_items = (
                admin_list_availability_slots(
                    db,
                    token=token,
                    professional_id=int(self.selected_professional),
                    start_date=self.filter_start_date,
                    end_date=self.filter_end_date,
                )
                if self.selected_professional != "__none__" else []
            )
            rule = (
                admin_get_weekly_schedule(
                    db, token=token, professional_id=int(self.selected_professional)
                )
                if self.selected_professional != "__none__" else None
            )
        self.professionals = professionals
        self.slots = _slot_rows(slot_items)
        if self.selected_calendar_day:
            try:
                day = datetime.strptime(self.selected_calendar_day, "%d/%m/%Y").date()
            except ValueError:
                self.selected_calendar_day = ""
            else:
                if day.strftime("%Y-%m") != self.calendar_month:
                    self.selected_calendar_day = ""
        self._apply_weekly_rule(rule)

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
            yield rx.toast.error(self.error_message, position="top-right")
            self.slots = []
        except Exception:
            self.error_message = "Não foi possível carregar a disponibilidade agora."
            self.slots = []
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def update_selected_professional(self, value: str):
        self._clear_feedback()
        if value not in {item["value"] for item in self.professionals}:
            self.error_message = "Selecione um médico ativo da lista."
            return
        previous_professional = self.selected_professional
        previous_filter = self.filter_professional
        self.selected_professional = value
        self.filter_professional = value
        self.selected_calendar_day = ""
        self.is_loading = True
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.selected_professional = previous_professional
            self.filter_professional = previous_filter
            self.error_message = "Não foi possível consultar a agenda deste médico."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def update_weekly_start_day(self, value: str) -> None:
        self.weekly_start_day = value

    @rx.event
    def update_weekly_end_day(self, value: str) -> None:
        self.weekly_end_day = value

    @rx.event
    def update_weekly_start_time(self, value: str) -> None:
        self.weekly_start_time = value

    @rx.event
    def update_weekly_end_time(self, value: str) -> None:
        self.weekly_end_time = value

    @rx.event
    def update_weekly_slot_minutes(self, value: str) -> None:
        self.weekly_slot_minutes = value

    @rx.event
    async def save_weekly(self, _form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if self.selected_professional == "__none__":
                raise SchedulingValidationError("Selecione o médico antes de configurar o expediente.")
            token = await self._token()
            with rx.session() as db:
                admin_save_weekly_schedule(
                    db, token=token, professional_id=int(self.selected_professional),
                    weekday_start=int(self.weekly_start_day),
                    weekday_end=int(self.weekly_end_day),
                    time_start=self.weekly_start_time,
                    time_end=self.weekly_end_time,
                    slot_minutes=int(self.weekly_slot_minutes),
                )
            self._load_with_token(token)
            yield rx.toast.success(
                "Expediente salvo. Disponibilidade atualizada para a janela de 45 dias.",
                position="top-right",
            )
        except (SchedulingValidationError, SchedulingConflictError,
                SchedulingTimeValidationError, ClinicTimezoneConfigurationError, ValueError) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível salvar o expediente. Confira o médico e os horários."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def update_slot_datetime(self, value: str) -> None:
        self.slot_datetime_local = value

    @rx.event
    def update_slot_date(self, value: str) -> None:
        self.slot_date_local = value

    @rx.event
    def update_slot_time(self, value: str) -> None:
        self.slot_time_local = value

    @rx.event
    def update_filter_professional(self, value: str):
        """Backward-compatible alias for legacy callers."""
        if value != "__all__":
            return AdminAvailabilityState.update_selected_professional(value)

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
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível atualizar a disponibilidade agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def create_slot(self, _form_data: dict[str, Any]):
        if self.is_submitting:
            return
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if self.selected_professional == "__none__":
                raise SchedulingValidationError("Selecione um profissional ativo.")
            token = await self._token()
            # Existing callers may still provide the combined field; the new
            # administrator form supplies separate date/time instead.
            if self.slot_date_local or self.slot_time_local:
                if not self.slot_date_local or not self.slot_time_local:
                    raise SchedulingValidationError("Informe a data e a hora do atendimento.")
                starts_at_local = f"{self.slot_date_local}T{self.slot_time_local}"
            elif self.slot_datetime_local:
                starts_at_local = self.slot_datetime_local
            else:
                raise SchedulingValidationError("Informe a data e a hora do atendimento.")
            with rx.session() as db:
                admin_create_availability_slot(
                    db,
                    token=token,
                    professional_id=int(self.selected_professional),
                    starts_at_local=starts_at_local,
                )
            self.slot_datetime_local = ""
            self.slot_date_local = ""
            self.slot_time_local = ""
            created_date = self.slot_date_local or starts_at_local[:10]
            self.calendar_month = created_date[:7]
            year, month = map(int, self.calendar_month.split("-"))
            self.filter_start_date = f"{year:04d}-{month:02d}-01"
            self.filter_end_date = f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
            self._load_with_token(token)
            from datetime import datetime
            self.selected_calendar_day = datetime.strptime(created_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            self.active_operation = "search"
            yield rx.toast.success("Horário disponibilizado.", position="top-right")
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingTimeValidationError,
            ClinicTimezoneConfigurationError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível criar o horário agora."
            yield rx.toast.error(self.error_message, position="top-right")
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def toggle_slot(self, slot_id: int, current_status: str):
        if self.is_submitting:
            return
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
            yield rx.toast.success("Horário reativado." if activate else "Horário desativado.", position="top-right")
        except (
            SchedulingTransitionError,
            SchedulingNotFoundError,
            SchedulingValidationError,
            ClinicTimezoneConfigurationError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível alterar o horário agora."
            yield rx.toast.error(self.error_message, position="top-right")
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
    agenda_date_input: str = ""
    selected_agenda_date: str = ""

    patient_cpf: str = ""
    selected_patient_id: int = 0
    selected_patient_name: str = ""

    # Navigation from patient selection can activate booking exactly once;
    # otherwise the Agenda opens with its existing consultations.
    active_tab: str = "consultations"
    consultation_page: int = 1
    consultation_page_size: int = 10
    focus_booking_on_next_load: bool = False

    booking_dialog_open: bool = False
    booking_discard_open: bool = False
    booking_step: int = 1
    booking_patient_query: str = ""
    booking_patients: list[BookingPatientRow] = []
    booking_professionals: list[BookingProfessionalRow] = []
    booking_professional: str = "__none__"
    booking_slots: list[SlotRow] = []
    booking_month: str = ""
    booking_date: str = ""
    booking_slot_id: int = 0
    booking_error_message: str = ""
    is_booking_loading: bool = False

    arrival_dialog_open: bool = False
    arrival_consultation_id: int = 0
    arrival_patient_name: str = ""
    arrival_professional_name: str = ""
    arrival_scheduled_at: str = ""
    arrival_symptoms: str = ""
    arrival_priority: str = "VERDE"

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
    def visible_consultations(self) -> list[ConsultationRow]:
        return filter_consultations_for_day(self.consultations, self.selected_agenda_date)

    @rx.var
    def agenda_week_days(self) -> list[AgendaWeekDay]:
        return build_week_days(
            self.consultations,
            self.filter_start_date or clinic_today_iso(),
            self.selected_agenda_date,
            clinic_today_iso(),
        )

    @rx.var
    def agenda_period_label(self) -> str:
        start, end = week_bounds(self.filter_start_date or clinic_today_iso())
        return f"{date.fromisoformat(start):%d/%m/%Y} a {date.fromisoformat(end):%d/%m/%Y}"

    @rx.var
    def selected_agenda_day_label(self) -> str:
        if not self.selected_agenda_date:
            return ""
        return date.fromisoformat(self.selected_agenda_date).strftime("%d/%m/%Y")

    @rx.var
    def consultation_total_pages(self) -> int:
        return max(1, (len(self.visible_consultations) + self.consultation_page_size - 1) // self.consultation_page_size)

    @rx.var
    def paged_consultations(self) -> list[ConsultationRow]:
        start = (self.consultation_page - 1) * self.consultation_page_size
        return self.visible_consultations[start:start + self.consultation_page_size]

    @rx.event
    def move_consultation_page(self, delta: int) -> None:
        self.consultation_page = max(1, min(
            self.consultation_page + delta, self.consultation_total_pages
        ))

    @rx.var
    def available_slots(self) -> list[SlotRow]:
        return [
            row
            for row in self.slots
            if row["status"] == AvailabilitySlotStatus.AVAILABLE.value
        ]

    @rx.var
    def available_slots_by_day(self) -> list[SlotDayGroup]:
        return group_slots_by_day(self.available_slots)

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
        self.selected_agenda_date = ""
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self.active_tab = "consultations"
        self.focus_booking_on_next_load = False
        self._reset_booking()
        self._reset_arrival()
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
        self.consultation_page = min(self.consultation_page, self.consultation_total_pages)

    def _set_agenda_week(self, first_day: str) -> None:
        self.filter_start_date, self.filter_end_date = week_bounds(first_day)
        self.agenda_date_input = self.filter_start_date
        self.selected_agenda_date = ""
        self.consultation_page = 1

    def _reset_arrival(self) -> None:
        self.arrival_dialog_open = False
        self.arrival_consultation_id = 0
        self.arrival_patient_name = ""
        self.arrival_professional_name = ""
        self.arrival_scheduled_at = ""
        self.arrival_symptoms = ""
        self.arrival_priority = "VERDE"

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

    def _begin_arrival_from_row(self, row: ConsultationRow) -> None:
        self._clear_feedback()
        self._reset_reschedule()
        self._reset_cancel()
        self.arrival_consultation_id = row["id"]
        self.arrival_patient_name = row["patient_name"]
        self.arrival_professional_name = row["professional_name"]
        self.arrival_scheduled_at = row["scheduled_at"]
        self.arrival_symptoms = ""
        self.arrival_priority = "VERDE"
        self.arrival_dialog_open = True

    def _begin_reschedule_from_row(self, row: ConsultationRow) -> None:
        self._clear_feedback()
        self._reset_arrival()
        self._reset_cancel()
        self.reschedule_consultation_id = row["id"]
        self.reschedule_patient_name = row["patient_name"]
        self.selected_new_slot = "__none__"
        self.reschedule_dialog_open = True

    def _begin_cancel_from_row(self, row: ConsultationRow) -> None:
        self._clear_feedback()
        self._reset_arrival()
        self._reset_reschedule()
        self.cancel_consultation_id = row["id"]
        self.cancel_patient_name = row["patient_name"]
        self.cancel_scheduled_at = row["scheduled_at"]
        self.cancel_dialog_open = True

    async def _refresh_daily_dashboard_if_loaded(self):
        """Keep the daily workspace current after an action opened from its menu."""
        from vitta_one.reception.dashboard.state import ReceptionDashboardState

        dashboard = await self.get_state(ReceptionDashboardState)
        if dashboard.has_loaded:
            async for event in dashboard.refresh():
                yield event

    def _current_consultation(self, consultation_id: int) -> ConsultationRow:
        row = next(
            (item for item in self.consultations if item["id"] == consultation_id),
            None,
        )
        if row is None:
            raise SchedulingNotFoundError(
                "A consulta não está mais na agenda atualizada."
            )
        return row

    async def _authorization_redirect(self, exc: Exception):
        self._clear_sensitive()
        if isinstance(exc, AuthenticationRequiredError):
            yield rx.redirect("/login")
        else:
            yield rx.redirect("/acesso-negado")

    @rx.event
    def change_active_tab(self, value: str) -> None:
        self.active_tab = "consultations"

    @rx.event
    async def load(self):
        open_from_patient = self.focus_booking_on_next_load
        self.active_tab = "consultations"
        self.focus_booking_on_next_load = False
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
            if open_from_patient:
                self._reset_booking(preserve_patient=True)
                self._load_booking_professionals_with_token(token)
                self.booking_dialog_open = True
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
    async def load_agenda(self):
        """Load a single seven-day clinic-local window for both views."""
        try:
            start = self.filter_start_date or clinic_today_iso()
            self._set_agenda_week(start)
        except (ValueError, OverflowError):
            self._set_agenda_week(clinic_today_iso())
        async for event in self.load():
            yield event

    @rx.event
    def update_agenda_date_input(self, value: str) -> None:
        self.agenda_date_input = value

    @rx.event
    async def apply_agenda_date(self):
        try:
            self._set_agenda_week(self.agenda_date_input)
        except (ValueError, OverflowError):
            self.error_message = "Informe uma data inicial válida."
            return
        async for event in self.refresh():
            yield event

    @rx.event
    async def move_agenda_week(self, delta: int):
        if delta not in (-1, 1):
            return
        try:
            first = date.fromisoformat(self.filter_start_date or clinic_today_iso())
            self._set_agenda_week((first + timedelta(days=7 * delta)).isoformat())
        except (ValueError, OverflowError):
            self.error_message = "Não foi possível navegar para esse período."
            return
        async for event in self.refresh():
            yield event

    @rx.event
    async def go_to_agenda_today(self):
        self._set_agenda_week(clinic_today_iso())
        async for event in self.refresh():
            yield event

    @rx.event
    async def clear_agenda_filters(self):
        self.filter_professional = "__all__"
        self._set_agenda_week(clinic_today_iso())
        async for event in self.refresh():
            yield event

    @rx.event
    def select_agenda_day(self, day_iso: str) -> None:
        try:
            day = date.fromisoformat(day_iso)
            start = date.fromisoformat(self.filter_start_date)
            if not start <= day <= start + timedelta(days=6):
                return
        except ValueError:
            return
        self.selected_agenda_date = "" if self.selected_agenda_date == day_iso else day_iso
        self.consultation_page = 1

    @rx.event
    def clear_agenda_day(self) -> None:
        self.selected_agenda_date = ""
        self.consultation_page = 1

    @rx.event
    def update_filter_professional(self, value: str) -> None:
        self.filter_professional = value
        self.consultation_page = 1

    @rx.event
    def update_filter_start_date(self, value: str) -> None:
        self.filter_start_date = value
        self.consultation_page = 1

    @rx.event
    def update_filter_end_date(self, value: str) -> None:
        self.filter_end_date = value
        self.consultation_page = 1

    @rx.event
    def reset_consultation_page(self) -> None:
        self.consultation_page = 1

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
    async def find_patient(self, _form_data: dict[str, Any]):
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
            yield rx.toast.success(self.success_message, position="top-right")
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

    @rx.var
    def booking_professional_name(self) -> str:
        return next((row["label"] for row in self.booking_professionals
                     if row["value"] == self.booking_professional), "")

    @rx.var
    def booking_specialties(self) -> str:
        return next((row["specialties"] for row in self.booking_professionals
                     if row["value"] == self.booking_professional), "")

    @rx.var
    def booking_month_title(self) -> str:
        try:
            year, month = map(int, self.booking_month.split("-"))
            return f"{('Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro')[month - 1]} {year}"
        except (ValueError, IndexError):
            return ""

    @rx.var
    def booking_calendar_days(self) -> list[AdminCalendarCell]:
        return booking_calendar_cells(
            self.booking_slots, self.booking_month, self.booking_date,
            clinic_today_iso(), clinic_date_after_iso(44),
        )

    @rx.var
    def booking_can_move_previous_month(self) -> bool:
        return bool(self.booking_month) and self.booking_month > clinic_today_iso()[:7]

    @rx.var
    def booking_can_move_next_month(self) -> bool:
        return bool(self.booking_month) and self.booking_month < clinic_date_after_iso(44)[:7]

    @rx.var
    def booking_date_slots(self) -> list[SlotRow]:
        return [slot for slot in self.booking_slots if
                slot["date_label"] == self.booking_date
                and slot["status"] == AvailabilitySlotStatus.AVAILABLE.value]

    @rx.var
    def booking_slot_label(self) -> str:
        return next((slot["starts_at"] for slot in self.booking_slots
                     if slot["id"] == self.booking_slot_id), "")

    def _reset_booking(self, *, preserve_patient: bool = False) -> None:
        if not preserve_patient:
            self.selected_patient_id = 0
            self.selected_patient_name = ""
        self.booking_dialog_open = False
        self.booking_discard_open = False
        self.booking_step = 1
        self.booking_patient_query = ""
        self.booking_patients = []
        self.booking_professionals = []
        self.booking_professional = "__none__"
        self.booking_slots = []
        self.booking_month = clinic_today_iso()[:7]
        self.booking_date = ""
        self.booking_slot_id = 0
        self.booking_error_message = ""
        self.is_booking_loading = False

    def _load_booking_professionals_with_token(self, token: str) -> None:
        with rx.session() as db:
            rows = reception_list_booking_professionals(db, token=token)
        self.booking_professionals = [
            {"id": professional.id, "value": str(professional.id),
             "label": professional.name, "specialties": specialties}
            for professional, specialties in rows
        ]

    def _load_booking_slots_with_token(self, token: str) -> None:
        if not self.booking_professional.isdecimal():
            self.booking_slots = []
            return
        with rx.session() as db:
            snapshot = reception_get_agenda(
                db, token=token,
                professional_id=int(self.booking_professional),
                start_date=clinic_today_iso(), end_date=clinic_date_after_iso(44),
            )
        now = datetime.now(timezone.utc)
        self.booking_slots = _slot_rows([
            slot for slot in snapshot.slots
            if slot.status is AvailabilitySlotStatus.AVAILABLE and slot.starts_at > now
        ])
        if self.booking_date and not any(
            slot["date_label"] == self.booking_date for slot in self.booking_slots
        ):
            self.booking_date = ""
            self.booking_slot_id = 0
        elif self.booking_slot_id and not any(
            slot["id"] == self.booking_slot_id for slot in self.booking_slots
        ):
            self.booking_slot_id = 0

    def _request_booking_close(self) -> None:
        if self.is_submitting:
            return
        if (self.selected_patient_id or self.booking_patient_query.strip()
                or self.booking_professional != "__none__"):
            self.booking_discard_open = True
        else:
            self._reset_booking()

    @rx.event
    async def open_booking(self):
        if self.is_submitting:
            return
        self._reset_booking()
        self.is_booking_loading = True
        yield
        try:
            token = await self._token()
            self._load_booking_professionals_with_token(token)
            self.booking_dialog_open = True
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            yield rx.toast.error(
                "Não foi possível iniciar o agendamento. Tente novamente.",
                position="top-right",
            )
        finally:
            self.is_booking_loading = False
            yield

    @rx.event
    def set_booking_dialog_open(self, is_open: bool) -> None:
        if is_open:
            self.booking_dialog_open = True
        else:
            self._request_booking_close()

    @rx.event
    def cancel_booking(self) -> None:
        self._request_booking_close()

    @rx.event
    def set_booking_discard_open(self, is_open: bool) -> None:
        self.booking_discard_open = is_open

    @rx.event
    def discard_booking(self) -> None:
        self._reset_booking()

    @rx.event
    def update_booking_patient_query(self, value: str) -> None:
        self.booking_patient_query = str(value or "")[:100]
        self.booking_patients = []
        self.booking_error_message = ""

    @rx.event
    async def search_booking_patients(self, form_data: dict[str, Any]):
        self.booking_patient_query = str(
            form_data.get("query", self.booking_patient_query) or ""
        )[:100]
        if len(self.booking_patient_query.strip()) < 2:
            self.booking_error_message = "Digite ao menos 2 caracteres para buscar pacientes."
            return
        self.is_booking_loading = True
        self.booking_error_message = ""
        self.booking_patients = []
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                results = reception_search_patients(
                    db, token=token, query=self.booking_patient_query, limit=8
                )
            self.booking_patients = [
                {"id": item.id, "name": item.name,
                 "contact_hint": _masked_booking_contact(item.phone)}
                for item in results
            ]
            if not results:
                self.booking_error_message = "Nenhum paciente encontrado para esta busca."
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.booking_error_message = "Não foi possível buscar pacientes agora."
        finally:
            self.is_booking_loading = False
            yield

    @rx.event
    async def select_booking_patient(self, patient_id: int):
        self.booking_error_message = ""
        try:
            token = await self._token()
            with rx.session() as db:
                patient = reception_get_patient_identity(
                    db, token=token, patient_id=patient_id,
                )
            if patient is None:
                raise SchedulingValidationError("Paciente não encontrado. Faça outra busca.")
            self.selected_patient_id = patient.id
            self.selected_patient_name = patient.name
            self.booking_patients = []
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except SchedulingValidationError as exc:
            self.booking_error_message = str(exc)
        except Exception:
            self.booking_error_message = "Não foi possível selecionar o paciente."

    @rx.event
    def clear_booking_patient(self) -> None:
        self.selected_patient_id = 0
        self.selected_patient_name = ""
        self.booking_error_message = ""

    @rx.event
    async def choose_booking_professional(self, value: str):
        self.booking_professional = value if any(
            row["value"] == value for row in self.booking_professionals
        ) else "__none__"
        self.booking_date = ""
        self.booking_slot_id = 0
        self.booking_slots = []
        self.booking_month = clinic_today_iso()[:7]
        self.booking_error_message = ""
        if self.booking_professional == "__none__":
            return
        self.is_booking_loading = True
        yield
        try:
            token = await self._token()
            self._load_booking_slots_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.booking_error_message = "Não foi possível consultar a disponibilidade."
        finally:
            self.is_booking_loading = False
            yield

    @rx.event
    def move_booking_month(self, delta: int) -> None:
        try:
            year, month = map(int, self.booking_month.split("-"))
            next_month = date(year + (month - 1 + delta) // 12,
                              (month - 1 + delta) % 12 + 1, 1).strftime("%Y-%m")
            if clinic_today_iso()[:7] <= next_month <= clinic_date_after_iso(44)[:7]:
                self.booking_month = next_month
                self.booking_date = ""
                self.booking_slot_id = 0
                self.booking_error_message = ""
        except (ValueError, IndexError):
            return

    @rx.event
    async def choose_booking_date(self, value: str):
        if not any(day["date_label"] == value and day["has_slots"]
                   for day in self.booking_calendar_days):
            self.booking_error_message = "Selecione uma data com horários disponíveis."
            return
        self.booking_date = value
        self.booking_slot_id = 0
        self.booking_error_message = ""
        self.is_booking_loading = True
        yield
        try:
            token = await self._token()
            self._load_booking_slots_with_token(token)
            if not self.booking_date:
                self.booking_error_message = (
                    "A disponibilidade deste dia mudou. Escolha outra data."
                )
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.booking_error_message = "Não foi possível atualizar os horários."
        finally:
            self.is_booking_loading = False
            yield

    @rx.event
    def choose_booking_slot(self, slot_id: int) -> None:
        if any(item["id"] == slot_id for item in self.booking_date_slots):
            self.booking_slot_id = slot_id
            self.booking_error_message = ""
        else:
            self.booking_slot_id = 0
            self.booking_error_message = "Este horário deixou de estar disponível."

    @rx.event
    async def refresh_booking_availability(self):
        if self.booking_professional == "__none__":
            return
        self.is_booking_loading = True
        self.booking_error_message = ""
        yield
        try:
            token = await self._token()
            self._load_booking_slots_with_token(token)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.booking_error_message = "Não foi possível atualizar a disponibilidade."
        finally:
            self.is_booking_loading = False
            yield

    @rx.event
    def booking_next(self) -> None:
        if self.is_submitting or self.is_booking_loading:
            return
        messages = {
            1: (self.selected_patient_id > 0, "Selecione um paciente para continuar."),
            2: (self.booking_professional != "__none__", "Selecione um médico."),
            3: (bool(self.booking_date and self.booking_date_slots), "Selecione um dia disponível."),
            4: (self.booking_slot_id > 0 and bool(self.booking_slot_label),
                "Selecione um horário disponível."),
        }
        valid, message = messages.get(self.booking_step, (False, "Etapa inválida."))
        if not valid:
            self.booking_error_message = message
            return
        self.booking_error_message = ""
        self.booking_step = min(5, self.booking_step + 1)

    @rx.event
    def booking_back(self) -> None:
        if not self.is_submitting:
            self.booking_step = max(1, self.booking_step - 1)
            self.booking_error_message = ""

    @rx.event
    async def confirm_booking(self):
        if self.is_submitting:
            return
        self.is_submitting = True
        self.booking_error_message = ""
        yield
        token = ""
        try:
            if self.booking_step != 5 or not self.selected_patient_id:
                raise SchedulingValidationError("Revise o paciente antes de confirmar.")
            slot = next(
                (row for row in self.booking_date_slots
                 if row["id"] == self.booking_slot_id), None
            )
            if (slot is None or str(slot["professional_id"]) != self.booking_professional):
                raise SchedulingValidationError("Revise médico, data e horário antes de confirmar.")
            token = await self._token()
            with rx.session() as db:
                reception_schedule_consultation(
                    db, token=token,
                    patient_id=self.selected_patient_id,
                    slot_id=self.booking_slot_id,
                )
            booked_date_iso = datetime.strptime(self.booking_date, "%d/%m/%Y").date().isoformat()
            if self.filter_professional not in ("__all__", self.booking_professional):
                self.filter_professional = self.booking_professional
            if not self.filter_start_date or booked_date_iso < self.filter_start_date:
                self.filter_start_date = booked_date_iso
            if not self.filter_end_date or booked_date_iso > self.filter_end_date:
                self.filter_end_date = booked_date_iso
            self.consultation_page = 1
            self._reset_booking()
            self.success_message = "Consulta agendada com sucesso"
            yield rx.toast.success(self.success_message, position="top-right")
            try:
                self._load_with_token(token)
            except Exception:
                # Reservation was already committed; never offer an unsafe retry.
                yield rx.toast.warning(
                    "Consulta salva. Não foi possível atualizar a lista agora.",
                    position="top-right",
                )
            try:
                async for event in self._refresh_daily_dashboard_if_loaded():
                    yield event
            except Exception:
                # The booking is already committed; a read-only refresh must not
                # turn success into an error that encourages a duplicate submit.
                yield rx.toast.warning(
                    "Consulta salva. Atualize o painel para visualizar os indicadores.",
                    position="top-right",
                )
        except (SchedulingConflictError, SchedulingNotFoundError) as exc:
            self.booking_error_message = str(exc)
            self.booking_slot_id = 0
            if token:
                try:
                    self._load_booking_slots_with_token(token)
                except Exception:
                    self.booking_slots = []
                    self.booking_date = ""
            self.booking_step = 4 if self.booking_date and self.booking_date_slots else 3
            yield rx.toast.error(self.booking_error_message, position="top-right")
        except (SchedulingValidationError, SchedulingTimeValidationError) as exc:
            self.booking_error_message = str(exc)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.booking_error_message = "Não foi possível agendar. Tente novamente."
        finally:
            self.is_submitting = False
            yield

    @rx.event
    async def download_appointment_calendar(self, consultation_id: int):
        """Download an .ics file only after authorized re-read of the appointment."""
        try:
            token = await self._token()
            with rx.session() as db:
                item = reception_get_consultation_by_id(
                    db, token=token, consultation_id=consultation_id
                )
            calendar_data = build_consultation_ics(item)
            yield rx.download(
                data=calendar_data,
                filename=f"vitta-one-consulta-{item.id}.ics",
            )
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (SchedulingNotFoundError, ValueError) as exc:
            yield rx.toast.error(str(exc), position="top-right")
        except Exception:
            yield rx.toast.error(
                "Não foi possível preparar o calendário da consulta.",
                position="top-right",
            )

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
            booked_slot = next((item for item in self.slots if item["id"] == slot_id), None)
            if booked_slot is not None:
                booked_day = datetime.strptime(
                    booked_slot["starts_at"], "%d/%m/%Y às %H:%M"
                ).date().isoformat()
                self._set_agenda_week(booked_day)
            self._load_with_token(token)
            self.success_message = "Consulta agendada."
            yield rx.toast.success(self.success_message, position="top-right")
            yield rx.redirect("/recepcao/agenda")
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingNotFoundError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível agendar a consulta agora."
            yield rx.toast.error(self.error_message, position="top-right")
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_arrival(
        self,
        consultation_id: int,
        patient_name: str,
        professional_name: str,
        scheduled_at: str,
    ) -> None:
        self._begin_arrival_from_row(
            {
                "id": consultation_id,
                "patient_id": 0,
                "patient_name": patient_name,
                "professional_id": 0,
                "professional_name": professional_name,
                "slot_id": 0,
                "scheduled_at": scheduled_at,
                "status": ConsultationStatus.AGENDADA.value,
                "status_label": ConsultationStatus.AGENDADA.label,
            }
        )

    @rx.event
    async def open_arrival_from_daily_operations(self, consultation_id: int):
        """Revalidate a daily row before opening the existing arrival flow."""
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                consultation = reception_get_consultation_by_id(
                    db, token=token, consultation_id=consultation_id
                )
            row = _consultation_rows([consultation])[0]
            if row["status"] != ConsultationStatus.AGENDADA.value:
                raise SchedulingTransitionError(
                    "A chegada só pode ser confirmada para uma consulta agendada."
                )
            self._begin_arrival_from_row(row)
            yield
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (SchedulingNotFoundError, SchedulingTransitionError) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except Exception:
            self.error_message = "Não foi possível abrir a confirmação de chegada."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def set_arrival_dialog_open(self, is_open: bool) -> None:
        if self.is_submitting and not is_open:
            return
        self.arrival_dialog_open = is_open
        if not is_open:
            self._reset_arrival()

    @rx.event
    def update_arrival_symptoms(self, value: str) -> None:
        self.arrival_symptoms = value

    @rx.event
    def update_arrival_priority(self, value: str) -> None:
        self.arrival_priority = value

    @rx.event
    async def confirm_arrival(self, _form_data: dict[str, Any]):
        self.is_submitting = True
        self._clear_feedback()
        yield
        try:
            if not self.arrival_consultation_id:
                raise CareLifecycleValidationError("Selecione uma consulta agendada.")
            token = await self._token()
            with rx.session() as db:
                reception_confirm_arrival(
                    db,
                    token=token,
                    consultation_id=self.arrival_consultation_id,
                    symptoms=self.arrival_symptoms,
                    priority=self.arrival_priority,
                )
            self._reset_arrival()
            self._load_with_token(token)
            queue_state = await self.get_state(ReceptionQueueState)
            queue_state._load_queue_with_token(token)
            self.success_message = "Chegada confirmada e paciente incluído na fila."
            yield rx.toast.success(self.success_message, position="top-right")
            async for event in self._refresh_daily_dashboard_if_loaded():
                yield event
        except (
            CareLifecycleValidationError,
            CareLifecycleTransitionError,
            CareLifecycleConflictError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível confirmar a chegada agora."
            yield rx.toast.error(self.error_message, position="top-right")
        finally:
            self.is_submitting = False
            yield

    @rx.event
    def begin_reschedule(self, consultation_id: int, patient_name: str) -> None:
        self._begin_reschedule_from_row(
            {
                "id": consultation_id,
                "patient_id": 0,
                "patient_name": patient_name,
                "professional_id": 0,
                "professional_name": "",
                "slot_id": 0,
                "scheduled_at": "",
                "status": ConsultationStatus.AGENDADA.value,
                "status_label": ConsultationStatus.AGENDADA.label,
            }
        )

    @rx.event
    async def open_reschedule_from_daily_operations(self, consultation_id: int):
        """Load authorized availability and verify the consultation before opening."""
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                consultation = reception_get_consultation_by_id(
                    db, token=token, consultation_id=consultation_id
                )
                # Daily actions must never inherit unrelated Agenda filters.
                snapshot = reception_get_agenda(
                    db,
                    token=token,
                    professional_id=consultation.professional_id,
                    start_date=clinic_today_iso(),
                    end_date=clinic_date_after_iso(14),
                )
            self.slots = _slot_rows(snapshot.slots)
            row = _consultation_rows([consultation])[0]
            if row["status"] != ConsultationStatus.AGENDADA.value:
                raise SchedulingTransitionError(
                    "Somente consultas agendadas podem ser reagendadas."
                )
            self._begin_reschedule_from_row(row)
            yield
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (SchedulingNotFoundError, SchedulingTransitionError) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except Exception:
            self.error_message = "Não foi possível abrir o reagendamento agora."
        finally:
            self.is_loading = False
            yield

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
            yield rx.toast.success(self.success_message, position="top-right")
            async for event in self._refresh_daily_dashboard_if_loaded():
                yield event
        except (
            SchedulingValidationError,
            SchedulingConflictError,
            SchedulingNotFoundError,
            SchedulingTransitionError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível reagendar a consulta agora."
            yield rx.toast.error(self.error_message, position="top-right")
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
        self._begin_cancel_from_row(
            {
                "id": consultation_id,
                "patient_id": 0,
                "patient_name": patient_name,
                "professional_id": 0,
                "professional_name": "",
                "slot_id": 0,
                "scheduled_at": scheduled_at,
                "status": ConsultationStatus.AGENDADA.value,
                "status_label": ConsultationStatus.AGENDADA.label,
            }
        )

    @rx.event
    async def open_cancel_from_daily_operations(self, consultation_id: int):
        """Revalidate a daily row before opening the existing cancellation flow."""
        self.is_loading = True
        self._clear_feedback()
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                consultation = reception_get_consultation_by_id(
                    db, token=token, consultation_id=consultation_id
                )
            row = _consultation_rows([consultation])[0]
            if row["status"] != ConsultationStatus.AGENDADA.value:
                raise SchedulingTransitionError(
                    "Somente consultas agendadas podem ser canceladas."
                )
            self._begin_cancel_from_row(row)
            yield
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except (SchedulingNotFoundError, SchedulingTransitionError) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except Exception:
            self.error_message = "Não foi possível abrir o cancelamento agora."
        finally:
            self.is_loading = False
            yield

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
            async for event in self._refresh_daily_dashboard_if_loaded():
                yield event
        except (
            SchedulingValidationError,
            SchedulingNotFoundError,
            SchedulingTransitionError,
        ) as exc:
            self.error_message = str(exc)
            yield rx.toast.error(self.error_message, position="top-right")
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            async for event in self._authorization_redirect(exc):
                yield event
        except Exception:
            self.error_message = "Não foi possível cancelar a consulta agora."
            yield rx.toast.error(self.error_message, position="top-right")
        finally:
            self.is_submitting = False
            yield
