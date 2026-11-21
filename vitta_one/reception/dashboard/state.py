"""State for the receptionist's daily appointments workspace."""

from datetime import date, datetime, timedelta
from typing import Any, TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.settings import clinic_timezone
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    PasswordChangeRequiredError,
    RoleForbiddenError,
)
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.state import ReceptionQueueState
from vitta_one.reception.dashboard.application import (
    reception_day_operations,
    reception_email_metrics,
    reception_overview,
)


_WEEKDAYS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)
_MONTHS = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)


class ProfessionalOptionRow(TypedDict):
    value: str
    label: str


class ReceptionAppointmentRow(TypedDict):
    id: int
    time: str
    patient_name: str
    patient_phone: str
    professional_name: str
    specialty_name: str
    status_value: str
    status_label: str


def _format_phone(value: str | None) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return "Telefone não informado"


def _clinic_time_label(value: datetime) -> str:
    return value.astimezone(clinic_timezone()).strftime("%H:%M")


def _clinic_day_label(value: str) -> str:
    day = date.fromisoformat(value)
    weekday = _WEEKDAYS[day.weekday()].capitalize()
    return f"{weekday}, {day.day} de {_MONTHS[day.month - 1]}"


class AgendaEntry(TypedDict):
    id: int
    time: str
    patient_name: str
    professional_name: str


class AgendaDay(TypedDict):
    day_label: str
    date_label: str
    entries: list[AgendaEntry]


class UpcomingAppointmentRow(TypedDict):
    id: int
    date_label: str
    time: str
    patient_name: str
    professional_name: str
    status_label: str


class ReceptionDashboardState(rx.State):
    """Daily operational state; all reads revalidate receptionist authorization."""

    appointments: list[ReceptionAppointmentRow] = []
    overview_scheduled: int = 0
    overview_cancelled: int = 0
    overview_waiting: int = 0
    overview_attending: int = 0
    overview_pending: int = 0
    overview_completed: int = 0
    email_accepted: int = 0
    email_delivered: int = 0
    email_failed: int = 0
    email_pending: int = 0
    calendar_week: list[AgendaDay] = []
    upcoming_appointments: list[UpcomingAppointmentRow] = []
    professional_options: list[ProfessionalOptionRow] = []
    search_query: str = ""
    status_filter: str = "__all__"
    reload_generation: int = 0
    current_page: int = 1
    page_size: int = 8
    total_pages: int = 1
    total_count: int = 0
    clinic_date_label: str = ""
    last_updated: str = ""
    has_loaded: bool = False
    is_loading: bool = False
    error_message: str = ""
    details_dialog_open: bool = False
    details_patient_name: str = ""
    details_patient_phone: str = ""
    details_professional_name: str = ""
    details_specialty_name: str = ""
    details_time: str = ""
    details_status_value: str = ""
    details_status_label: str = ""

    @rx.var
    def has_appointments(self) -> bool:
        return bool(self.appointments)

    @rx.var
    def has_active_filters(self) -> bool:
        return bool(self.search_query.strip()) or self.status_filter != "__all__"

    @rx.var
    def showing_start(self) -> int:
        if self.total_count == 0:
            return 0
        return (self.current_page - 1) * self.page_size + 1

    @rx.var
    def showing_end(self) -> int:
        if self.total_count == 0:
            return 0
        return min(self.current_page * self.page_size, self.total_count)

    @rx.var
    def page_label(self) -> str:
        return f"{self.current_page} de {self.total_pages}"

    @rx.var
    def page_numbers(self) -> list[int]:
        """Return a bounded window of real server-side page numbers."""
        total = max(1, self.total_pages)
        start = max(1, min(self.current_page - 2, total - 4))
        end = min(total, start + 4)
        return list(range(start, end + 1))

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear_data(self) -> None:
        self.appointments = []
        self.calendar_week = []
        self.upcoming_appointments = []
        self.overview_scheduled = 0
        self.overview_cancelled = 0
        self.overview_waiting = 0
        self.overview_attending = 0
        self.overview_pending = 0
        self.overview_completed = 0
        self.email_accepted = 0
        self.email_delivered = 0
        self.email_failed = 0
        self.email_pending = 0
        self.professional_options = []
        self.total_count = 0
        self.total_pages = 1
        self.current_page = 1
        self.clinic_date_label = ""
        self.last_updated = ""
        self.has_loaded = False
        self._clear_details()

    def _clear_details(self) -> None:
        self.details_dialog_open = False
        self.details_patient_name = ""
        self.details_patient_phone = ""
        self.details_professional_name = ""
        self.details_specialty_name = ""
        self.details_time = ""
        self.details_status_value = ""
        self.details_status_label = ""

    def _apply_snapshot(self, snapshot) -> None:
        self.appointments = [
            {
                "id": item.id,
                "time": _clinic_time_label(item.scheduled_at),
                "patient_name": item.patient_name,
                "patient_phone": _format_phone(item.patient_phone),
                "professional_name": item.professional_name,
                "specialty_name": (
                    " · ".join(item.specialty_names)
                    if item.specialty_names
                    else "Especialidade não cadastrada"
                ),
                "status_value": item.status.value,
                "status_label": item.status.label,
            }
            for item in snapshot.appointments
        ]
        self.professional_options = [
            {"value": str(item.id), "label": item.name}
            for item in snapshot.professionals
        ]
        self.current_page = snapshot.page
        self.page_size = snapshot.page_size
        self.total_count = snapshot.total
        self.total_pages = snapshot.total_pages
        self.clinic_date_label = _clinic_day_label(snapshot.clinic_date)
        self.last_updated = format_clinic_datetime(snapshot.as_of)
        self.has_loaded = True

    def _apply_overview(self, overview):
        """Build persisted real-time cards and a seven-day calendar."""
        self.overview_scheduled = overview.scheduled_today
        self.overview_cancelled = overview.cancelled_today
        self.overview_waiting = overview.waiting
        self.overview_attending = overview.attending
        self.overview_pending = overview.arrivals_pending
        self.overview_completed = overview.finished_today
        start = date.fromisoformat(overview.clinic_date)
        events_by_date: dict[str, list[AgendaEntry]] = {}
        for appointment in overview.calendar_consultations:
            local_dt = appointment.scheduled_at.astimezone(clinic_timezone())
            key = local_dt.date().isoformat()
            events_by_date.setdefault(key, []).append({
                "id": appointment.id,
                "time": local_dt.strftime("%H:%M"),
                "patient_name": appointment.patient_name,
                "professional_name": appointment.professional_name,
            })
        self.calendar_week = [
            {
                "day_label": _WEEKDAYS[(start + timedelta(days=i)).weekday()].capitalize(),
                "date_label": (start + timedelta(days=i)).strftime("%d/%m"),
                "entries": events_by_date.get((start + timedelta(days=i)).isoformat(), []),
            }
            for i in range(7)
        ]
        upcoming: list[UpcomingAppointmentRow] = []
        for appointment in overview.calendar_consultations:
            if (appointment.scheduled_at < overview.as_of
                    or appointment.status == ConsultationStatus.CANCELADA):
                continue
            local_dt = appointment.scheduled_at.astimezone(clinic_timezone())
            days_ahead = (local_dt.date() - start).days
            date_label = (
                "Hoje" if days_ahead == 0
                else "Amanhã" if days_ahead == 1
                else local_dt.strftime("%d/%m")
            )
            upcoming.append({
                "id": appointment.id,
                "date_label": date_label,
                "time": local_dt.strftime("%H:%M"),
                "patient_name": appointment.patient_name,
                "professional_name": appointment.professional_name,
                "status_label": appointment.status.label,
            })
            # The dashboard keeps this card as a three-row preview; the full
            # appointment list remains available from the agenda route.
            if len(upcoming) == 3:
                break
        self.upcoming_appointments = upcoming

    def _apply_email_metrics(self, metrics) -> None:
        self.email_accepted = metrics.accepted
        self.email_delivered = metrics.delivered
        self.email_failed = metrics.failed
        self.email_pending = metrics.pending

    async def _reload(self):
        # A slow earlier search/page request must not replace a newer result.
        # Reflex events can overlap while the browser is processing consecutive
        # input, pagination, and periodic refresh events.
        self.reload_generation += 1
        generation = self.reload_generation
        search_query = self.search_query
        status_filter = self.status_filter
        current_page = self.current_page
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                snapshot = reception_day_operations(
                    db,
                    token=token,
                    search=search_query,
                    status=status_filter,
                    page=current_page,
                    page_size=8,
                )
                overview = reception_overview(db, token=token)
                email_metrics = reception_email_metrics(db, token=token)
            if generation != self.reload_generation:
                return
            self._apply_snapshot(snapshot)
            self._apply_overview(overview)
            self._apply_email_metrics(email_metrics)
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            if generation == self.reload_generation:
                self._clear_data()
                yield rx.redirect("/login")
        except RoleForbiddenError:
            if generation == self.reload_generation:
                self._clear_data()
                yield rx.redirect("/acesso-negado")
        except Exception:
            if generation == self.reload_generation:
                self._clear_data()
                self.error_message = (
                    "Não foi possível atualizar as consultas de hoje. Tente novamente."
                )
        finally:
            if generation == self.reload_generation:
                self.is_loading = False
                yield

    @rx.event
    async def load(self):
        async for event in self._reload():
            yield event

    @rx.event
    async def apply_search(self, form_data: dict[str, Any]):
        # Empty fields can be omitted by the browser's form serializer; an
        # explicit submit must still clear the previous server-side query.
        self.search_query = str(form_data.get("query") or "")[:100]
        self.current_page = 1
        async for event in self._reload():
            yield event

    @rx.event
    async def update_status(self, value: str):
        requested = str(value or "__all__")
        valid_statuses = {status.value for status in ConsultationStatus}
        self.status_filter = (
            requested if requested == "__all__" or requested in valid_statuses
            else "__all__"
        )
        self.current_page = 1
        async for event in self._reload():
            yield event

    @rx.event
    async def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            async for event in self._reload():
                yield event

    @rx.event
    async def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            async for event in self._reload():
                yield event

    @rx.event
    async def go_to_page(self, requested_page: int):
        """Change pages only within the last authorized server-side snapshot."""
        if (
            isinstance(requested_page, bool)
            or not isinstance(requested_page, int)
            or not 1 <= requested_page <= self.total_pages
        ):
            return
        if requested_page != self.current_page and not self.is_loading:
            self.current_page = requested_page
            async for event in self._reload():
                yield event

    @rx.event
    async def refresh(self):
        if self.is_loading:
            return
        async for event in self._reload():
            yield event
        yield ReceptionQueueState.load

    @rx.event
    async def tick(self, _value: str):
        """Refresh the overview periodically while the page is mounted."""
        if self.is_loading:
            return
        async for event in self._reload():
            yield event
        yield ReceptionQueueState.load

    @rx.event
    async def clear_filters(self):
        self.search_query = ""
        self.status_filter = "__all__"
        self.current_page = 1
        yield rx.call_script(
            "(() => { const input = document.getElementById('reception-day-search'); "
            "if (input) input.value = ''; })()"
        )
        async for event in self._reload():
            yield event

    @rx.event
    async def show_appointment_details(self, consultation_id: int):
        """Open a read-only operational summary from a fresh authorized snapshot."""
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                snapshot = reception_day_operations(
                    db,
                    token=token,
                    search=self.search_query,
                    status=self.status_filter,
                    page=self.current_page,
                    page_size=8,
                )
            self._apply_snapshot(snapshot)
            row = next(
                (item for item in self.appointments if item["id"] == consultation_id),
                None,
            )
            if row is None:
                self.error_message = (
                    "Esta consulta saiu da lista atualizada. Atualize e tente novamente."
                )
                self._clear_details()
                return
            self.details_patient_name = row["patient_name"]
            self.details_patient_phone = row["patient_phone"]
            self.details_professional_name = row["professional_name"]
            self.details_specialty_name = row["specialty_name"]
            self.details_time = row["time"]
            self.details_status_value = row["status_value"]
            self.details_status_label = row["status_label"]
            self.details_dialog_open = True
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear_data()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_data()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível abrir os detalhes operacionais agora."
        finally:
            self.is_loading = False
            yield

    @rx.event
    def set_details_dialog_open(self, is_open: bool) -> None:
        self.details_dialog_open = is_open
        if not is_open:
            self._clear_details()
