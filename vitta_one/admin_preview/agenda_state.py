"""Agenda administrativa em QA: somente projeções autorizadas, sem dados clínicos."""

import calendar
from collections import Counter
from datetime import date
from typing import TypedDict

import reflex as rx

from vitta_one.admin_preview.service import (
    AdminAgendaSnapshot,
    LocalAdminPreviewDisabledError,
    admin_agenda_snapshot,
)
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.temporal import clinic_today_iso, format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState


MONTH_NAMES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


class PreviewCalendarDay(TypedDict):
    date_label: str
    day: str
    is_current_month: bool
    is_selected: bool
    has_slots: bool
    slot_count: int
    consultation_count: int
    is_today: bool
    aria_label: str


class PreviewAgendaSlot(TypedDict):
    time_label: str
    professional_name: str
    status: str
    status_label: str


class PreviewAgendaConsultation(TypedDict):
    time_label: str
    professional_name: str
    status: str
    status_label: str


class PreviewProfessionalOption(TypedDict):
    value: str
    label: str


def build_preview_calendar_days(
    month: str,
    selected_day: str,
    today: str,
    slot_counts: Counter[str],
    consultation_counts: Counter[str],
) -> list[PreviewCalendarDay]:
    """Render one calendar month using counts of persisted records only."""
    year, month_number = map(int, month.split("-"))
    result: list[PreviewCalendarDay] = []
    for day in calendar.Calendar(firstweekday=6).itermonthdates(year, month_number):
        iso = day.isoformat()
        slots = slot_counts[iso]
        consultations = consultation_counts[iso]
        result.append({
            "date_label": iso,
            "day": str(day.day),
            "is_current_month": day.month == month_number,
            "is_selected": iso == selected_day,
            "has_slots": slots > 0 and day.month == month_number,
            "slot_count": slots,
            "consultation_count": consultations,
            "is_today": iso == today,
            "aria_label": (
                f"{day.strftime('%d/%m/%Y')}: {slots} horário(s), "
                f"{consultations} consulta(s)"
                + (", hoje" if iso == today else "")
            ),
        })
    return result


def _local_day(instant) -> str:
    """Use the same clinic timezone and formatter as appointment scheduling."""
    return date.fromisoformat(
        "-".join(reversed(format_clinic_datetime(instant).split(" às ")[0].split("/")))
    ).isoformat()


class AdminAgendaPreviewState(rx.State):
    """Independent read-only QA State; never loads the patient or clinical preview."""

    professionals: list[PreviewProfessionalOption] = []
    calendar_days: list[PreviewCalendarDay] = []
    day_slots: list[PreviewAgendaSlot] = []
    day_consultations: list[PreviewAgendaConsultation] = []
    filter_professional: str = "__all__"
    calendar_month: str = ""
    selected_day: str = ""
    is_loading: bool = False
    error_message: str = ""

    @rx.var
    def month_title(self) -> str:
        try:
            year, month = map(int, self.calendar_month.split("-"))
            return f"{MONTH_NAMES[month - 1]} {year}"
        except (ValueError, IndexError):
            return ""

    @rx.var
    def selected_day_label(self) -> str:
        try:
            return date.fromisoformat(self.selected_day).strftime("%d/%m/%Y")
        except ValueError:
            return ""

    @rx.var
    def available_count(self) -> int:
        return sum(row["status"] == AvailabilitySlotStatus.AVAILABLE.value for row in self.day_slots)

    @rx.var
    def booked_count(self) -> int:
        return sum(row["status"] == AvailabilitySlotStatus.BOOKED.value for row in self.day_slots)

    @rx.var
    def scheduled_count(self) -> int:
        return sum(row["status"] == ConsultationStatus.AGENDADA.value for row in self.day_consultations)

    @rx.var
    def cancelled_count(self) -> int:
        return sum(row["status"] == ConsultationStatus.CANCELADA.value for row in self.day_consultations)

    def _clear_results(self) -> None:
        self.calendar_days = []
        self.day_slots = []
        self.day_consultations = []

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _apply_snapshot(self, snapshot: AdminAgendaSnapshot) -> None:
        self.professionals = [
            {
                "value": str(item.id),
                "label": f"{item.name} · {item.registration_identifier}",
            }
            for item in snapshot.professionals
        ]
        selected = self.selected_day
        slot_counts: Counter[str] = Counter(
            _local_day(item.starts_at) for item in snapshot.slots
        )
        consultation_counts: Counter[str] = Counter(
            _local_day(item.scheduled_at) for item in snapshot.consultations
        )
        self.calendar_days = build_preview_calendar_days(
            self.calendar_month,
            selected,
            clinic_today_iso(),
            slot_counts,
            consultation_counts,
        )
        self.day_slots = [
            {
                "time_label": format_clinic_datetime(item.starts_at).split(" às ")[1],
                "professional_name": item.professional_name,
                "status": item.status.value,
                "status_label": item.status.label,
            }
            for item in snapshot.slots
            if _local_day(item.starts_at) == selected
        ]
        self.day_consultations = [
            {
                "time_label": format_clinic_datetime(item.scheduled_at).split(" às ")[1],
                "professional_name": item.professional_name,
                "status": item.status,
                "status_label": ConsultationStatus(item.status).label,
            }
            for item in snapshot.consultations
            if _local_day(item.scheduled_at) == selected
        ]

    def _load_with_token(self, token: str) -> None:
        year, month = map(int, self.calendar_month.split("-"))
        if not (2000 <= year <= 2100 and 1 <= month <= 12):
            raise ValueError("Período inválido.")
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        if not self.selected_day.startswith(self.calendar_month):
            self.selected_day = start_date
        # Não confiar em IDs fornecidos pelo navegador: o serviço verifica o vínculo.
        professional_id = (
            int(self.filter_professional)
            if self.filter_professional.isdecimal()
            else None
        )
        with rx.session() as db:
            snapshot = admin_agenda_snapshot(
                db,
                token=token,
                start_date=start_date,
                end_date=end_date,
                professional_id=professional_id,
            )
        self._apply_snapshot(snapshot)

    async def _reload(self):
        self.is_loading = True
        self.error_message = ""
        self._clear_results()
        yield
        try:
            token = await self._token()
            self._load_with_token(token)
        except LocalAdminPreviewDisabledError:
            self.professionals = []
            self._clear_results()
            yield rx.redirect(Role.ADMINISTRADOR.dashboard_path)
        except AuthenticationRequiredError:
            self.professionals = []
            self._clear_results()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self.professionals = []
            self._clear_results()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear_results()
            self.error_message = "Não foi possível consultar a agenda. Tente novamente."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def load_agenda(self):
        today = clinic_today_iso()
        self.calendar_month = today[:7]
        self.selected_day = today
        self.filter_professional = "__all__"
        async for event in self._reload():
            yield event

    @rx.event
    async def reload_agenda(self):
        async for event in self._reload():
            yield event

    @rx.event
    async def filter_by_professional(self, value: str):
        valid = {row["value"] for row in self.professionals}
        self.filter_professional = value if value == "__all__" or value in valid else "__all__"
        async for event in self._reload():
            yield event

    @rx.event
    async def move_month(self, delta: int):
        if delta not in (-1, 1):
            return
        year, month = map(int, self.calendar_month.split("-"))
        ordinal = year * 12 + month - 1 + delta
        new_year, month_index = divmod(ordinal, 12)
        if not 2000 <= new_year <= 2100:
            return
        self.calendar_month = f"{new_year:04d}-{month_index + 1:02d}"
        self.selected_day = f"{self.calendar_month}-01"
        async for event in self._reload():
            yield event

    @rx.event
    async def select_day(self, value: str):
        try:
            selected = date.fromisoformat(value)
            if selected.strftime("%Y-%m") != self.calendar_month:
                return
        except ValueError:
            return
        self.selected_day = value
        async for event in self._reload():
            yield event

    @rx.event
    async def clear_filters(self):
        self.filter_professional = "__all__"
        self.selected_day = clinic_today_iso()
        self.calendar_month = self.selected_day[:7]
        async for event in self._reload():
            yield event
