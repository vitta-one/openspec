"""State for the receptionist's daily appointments workspace."""

from datetime import date
from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import (
    AuthenticationRequiredError,
    PasswordChangeRequiredError,
    RoleForbiddenError,
)
from vitta_one.auth.state import AuthState
from vitta_one.reception.dashboard.application import reception_day_operations


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


def _clinic_day_label(value: str) -> str:
    day = date.fromisoformat(value)
    weekday = _WEEKDAYS[day.weekday()].capitalize()
    return f"{weekday}, {day.day} de {_MONTHS[day.month - 1]}"


class ReceptionDashboardState(rx.State):
    """Daily operational state; all reads revalidate receptionist authorization."""

    appointments: list[ReceptionAppointmentRow] = []
    professional_options: list[ProfessionalOptionRow] = []
    professional_filter: str = "__all__"
    search_query: str = ""
    current_page: int = 1
    page_size: int = 7
    total_pages: int = 1
    total_count: int = 0
    clinic_date_label: str = ""
    last_updated: str = ""
    has_loaded: bool = False
    is_loading: bool = False
    error_message: str = ""

    @rx.var
    def has_appointments(self) -> bool:
        return bool(self.appointments)

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

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _professional_filter_id(self) -> int | None:
        if self.professional_filter == "__all__":
            return None
        if not any(
            option["value"] == self.professional_filter
            for option in self.professional_options
        ):
            return None
        return int(self.professional_filter)

    def _clear_data(self) -> None:
        self.appointments = []
        self.professional_options = []
        self.total_count = 0
        self.total_pages = 1
        self.current_page = 1
        self.clinic_date_label = ""
        self.last_updated = ""
        self.has_loaded = False

    def _apply_snapshot(self, snapshot) -> None:
        self.appointments = [
            {
                "id": item.id,
                "time": item.scheduled_at.strftime("%H:%M"),
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
        if self.professional_filter != "__all__" and not any(
            option["value"] == self.professional_filter
            for option in self.professional_options
        ):
            self.professional_filter = "__all__"
        self.current_page = snapshot.page
        self.page_size = snapshot.page_size
        self.total_count = snapshot.total
        self.total_pages = snapshot.total_pages
        self.clinic_date_label = _clinic_day_label(snapshot.clinic_date)
        self.last_updated = format_clinic_datetime(snapshot.as_of)
        self.has_loaded = True

    async def _reload(self):
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                snapshot = reception_day_operations(
                    db,
                    token=token,
                    professional_id=self._professional_filter_id(),
                    search=self.search_query,
                    page=self.current_page,
                    page_size=7,
                )
            self._apply_snapshot(snapshot)
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear_data()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_data()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear_data()
            self.error_message = (
                "Não foi possível atualizar as consultas de hoje. Tente novamente."
            )
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def load(self):
        async for event in self._reload():
            yield event

    @rx.event
    def update_search_query(self, value: str) -> None:
        self.search_query = str(value or "")[:100]

    @rx.event
    async def apply_search(self, form_data: dict[str, str]):
        self.search_query = str(form_data.get("query", self.search_query) or "")[:100]
        self.current_page = 1
        async for event in self._reload():
            yield event

    @rx.event
    async def update_professional(self, value: str):
        requested = str(value or "__all__")
        if requested == "__all__" or any(
            option["value"] == requested for option in self.professional_options
        ):
            self.professional_filter = requested
        else:
            self.professional_filter = "__all__"
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
    async def refresh(self):
        async for event in self._reload():
            yield event
