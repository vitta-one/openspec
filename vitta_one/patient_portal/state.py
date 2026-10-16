"""Reflex state for the read-only patient consultation portal."""

from calendar import monthrange
from datetime import date
from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.application import patient_get_my_agenda
from vitta_one.appointment_scheduling.temporal import clinic_today_iso, format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState
from vitta_one.patient_portal.settings import clinic_location


class PatientConsultationRow(TypedDict):
    scheduled_at: str
    day_number: str
    professional_name: str
    specialty: str
    status: str
    rescheduled_from: str


class CalendarCell(TypedDict):
    day: str
    count: int


def _month_shift(value: str, offset: int) -> str:
    current = date.fromisoformat(f"{value}-01")
    index = current.year * 12 + current.month - 1 + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _month_label(value: date) -> str:
    names = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    return f"{names[value.month - 1].capitalize()} de {value.year}"


def _calendar_cells(month: str, rows: list[PatientConsultationRow]) -> list[CalendarCell]:
    year, month_num = (int(value) for value in month.split("-"))
    days = monthrange(year, month_num)[1]
    counts: dict[int, int] = {}
    for row in rows:
        day_num = int(row["day_number"])
        counts[day_num] = counts.get(day_num, 0) + 1
    cells: list[CalendarCell] = [{"day": "", "count": 0} for _ in range(date(year, month_num, 1).weekday())]
    cells.extend({"day": str(day), "count": counts.get(day, 0)} for day in range(1, days + 1))
    while len(cells) % 7:
        cells.append({"day": "", "count": 0})
    return cells


class PatientPortalState(rx.State):
    month: str = ""
    month_label: str = ""
    consultation_rows: list[PatientConsultationRow] = []
    calendar_cells: list[CalendarCell] = []
    clinic_name: str = ""
    clinic_address: str = ""
    location_configured: bool = False
    is_loading: bool = False
    error_message: str = ""

    @rx.var
    def has_consultations(self) -> bool:
        return bool(self.consultation_rows)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear(self) -> None:
        self.consultation_rows = []
        self.calendar_cells = []
        self.clinic_name = ""
        self.clinic_address = ""
        self.location_configured = False
        self.error_message = ""

    @rx.event
    async def load(self):
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            if not self.month:
                self.month = clinic_today_iso()[:7]
            month_date = date.fromisoformat(f"{self.month}-01")
            last_day = monthrange(month_date.year, month_date.month)[1]
            self.month_label = _month_label(month_date)
            location = clinic_location()
            self.location_configured = location.configured
            self.clinic_name = location.name if location.configured else ""
            self.clinic_address = location.address if location.configured else ""
            token = await self._token()
            with rx.session() as db:
                _patient, items = patient_get_my_agenda(
                    db,
                    token=token,
                    start_date=f"{self.month}-01",
                    end_date=f"{self.month}-{last_day:02d}",
                )
            rows: list[PatientConsultationRow] = []
            for item in items:
                previous = ""
                if item.schedule_changes:
                    previous = ", ".join(
                        format_clinic_datetime(old) for old, _new in item.schedule_changes
                    )
                formatted = format_clinic_datetime(item.scheduled_at)
                rows.append(
                    {
                        "scheduled_at": formatted,
                        "day_number": formatted[:2],
                        "professional_name": item.professional_name,
                        "specialty": ", ".join(item.specialty_names) or "Especialidade não informada",
                        "status": item.status.label,
                        "rescheduled_from": previous,
                    }
                )
            self.consultation_rows = rows
            self.calendar_cells = _calendar_cells(self.month, rows)
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            self._clear()
            if isinstance(exc, AuthenticationRequiredError):
                yield rx.redirect("/login")
            else:
                yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear()
            self.error_message = "Não foi possível carregar sua agenda agora. Atualize a página e tente novamente."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def previous_month(self):
        try:
            self.month = _month_shift(self.month or clinic_today_iso()[:7], -1)
        except Exception:
            self.month = clinic_today_iso()[:7]
        async for event in self.load():
            yield event

    @rx.event
    async def next_month(self):
        try:
            self.month = _month_shift(self.month or clinic_today_iso()[:7], 1)
        except Exception:
            self.month = clinic_today_iso()[:7]
        async for event in self.load():
            yield event


class AdminClinicConfigurationState(rx.State):
    """Public configuration status shown to the Administrator without fake defaults."""

    clinic_name: str = ""
    clinic_address: str = ""
    configured: bool = False

    @rx.event
    def load(self):
        location = clinic_location()
        self.configured = location.configured
        self.clinic_name = location.name if location.configured else ""
        self.clinic_address = location.address if location.configured else ""
