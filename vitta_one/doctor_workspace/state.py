"""Reflex state for the doctor's own agenda and consultation-derived roster."""

from calendar import monthrange
from datetime import date
from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.application import (
    doctor_get_my_agenda,
    doctor_list_my_patients,
)
from vitta_one.appointment_scheduling.service import SchedulingValidationError
from vitta_one.appointment_scheduling.temporal import clinic_today_iso, format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.state import AuthState


class DoctorConsultationRow(TypedDict):
    patient_name: str
    professional_name: str
    scheduled_at: str
    status: str
    specialty: str
    rescheduled_from: str


class DoctorPatientRow(TypedDict):
    name: str
    recent_consultation: str


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


def _calendar_cells(month: str, rows: list[DoctorConsultationRow]) -> list[CalendarCell]:
    year, month_num = (int(value) for value in month.split("-"))
    days = monthrange(year, month_num)[1]
    counts: dict[int, int] = {}
    for row in rows:
        try:
            day_num = int(row["scheduled_at"][:2])
        except (ValueError, TypeError):
            continue
        counts[day_num] = counts.get(day_num, 0) + 1
    cells: list[CalendarCell] = [{"day": "", "count": 0} for _ in range(date(year, month_num, 1).weekday())]
    cells.extend({"day": str(day), "count": counts.get(day, 0)} for day in range(1, days + 1))
    while len(cells) % 7:
        cells.append({"day": "", "count": 0})
    return cells


class DoctorWorkspaceState(rx.State):
    month: str = ""
    month_label: str = ""
    professional_name: str = ""
    consultation_rows: list[DoctorConsultationRow] = []
    patient_rows: list[DoctorPatientRow] = []
    calendar_cells: list[CalendarCell] = []
    is_loading: bool = False
    error_message: str = ""

    @rx.var
    def has_consultations(self) -> bool:
        return bool(self.consultation_rows)

    @rx.var
    def has_patients(self) -> bool:
        return bool(self.patient_rows)

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear(self) -> None:
        self.professional_name = ""
        self.consultation_rows = []
        self.patient_rows = []
        self.calendar_cells = []
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
            token = await self._token()
            with rx.session() as db:
                path = self.router.route_id
                if path == "/medico/pacientes":
                    professional, patients = doctor_list_my_patients(db, token=token)
                    self.professional_name = professional.name
                    self.patient_rows = [
                        {"name": name, "recent_consultation": format_clinic_datetime(scheduled_at)}
                        for _patient_id, name, scheduled_at in patients
                    ]
                    self.consultation_rows = []
                    self.calendar_cells = []
                else:
                    professional, items = doctor_get_my_agenda(
                        db,
                        token=token,
                        start_date=f"{self.month}-01",
                        end_date=f"{self.month}-{last_day:02d}",
                    )
                    self.professional_name = professional.name
                    rows = []
                    for item in items:
                        previous = ""
                        if item.schedule_changes:
                            previous = ", ".join(
                                format_clinic_datetime(old) for old, _new in item.schedule_changes
                            )
                        rows.append(
                            {
                                "patient_name": item.patient_name,
                                "professional_name": item.professional_name,
                                "scheduled_at": format_clinic_datetime(item.scheduled_at),
                                "status": item.status.label,
                                "specialty": ", ".join(item.specialty_names) or "Especialidade não informada",
                                "rescheduled_from": previous,
                            }
                        )
                    self.consultation_rows = rows
                    self.calendar_cells = _calendar_cells(self.month, rows)
                    self.patient_rows = []
        except (AuthenticationRequiredError, RoleForbiddenError) as exc:
            self._clear()
            if isinstance(exc, AuthenticationRequiredError):
                yield rx.redirect("/login")
            else:
                yield rx.redirect("/acesso-negado")
        except SchedulingValidationError as exc:
            self._clear()
            self.error_message = str(exc)
        except Exception:
            self._clear()
            self.error_message = "Não foi possível carregar seus dados agora. Atualize a página e tente novamente."
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
