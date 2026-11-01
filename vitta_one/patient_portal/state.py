"""Reflex state for the read-only patient consultation portal."""

from calendar import monthrange
from datetime import date
from typing import TypedDict

import reflex as rx

from vitta_one.appointment_scheduling.application import patient_get_my_agenda
from vitta_one.appointment_scheduling.temporal import clinic_today_iso, format_clinic_datetime
from vitta_one.auth.authorization import (
    AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError, require_role,
)
from vitta_one.auth.roles import Role
from vitta_one.clinic_settings.service import (
    ClinicSettingsConflictError, ClinicSettingsValidationError,
    get_clinic_location, save_clinic_location,
)
from vitta_one.auth.state import AuthState


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
            token = await self._token()
            with rx.session() as db:
                _patient, items = patient_get_my_agenda(
                    db,
                    token=token,
                    start_date=f"{self.month}-01",
                    end_date=f"{self.month}-{last_day:02d}",
                )
                location = get_clinic_location(db)
            self.location_configured = location.configured
            self.clinic_name = location.name if location.configured else ""
            self.clinic_address = location.address if location.configured else ""
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
    """Authorized editing of persisted public clinic information."""

    clinic_name: str = ""
    clinic_address: str = ""
    configured: bool = False
    revision: int = 0
    is_loading: bool = True
    is_saving: bool = False
    load_failed: bool = False
    name_error: str = ""
    address_error: str = ""
    error_message: str = ""
    success_message: str = ""

    async def _token(self) -> str:
        auth = await self.get_state(AuthState)
        return auth.session_token

    def _clear(self) -> None:
        self.clinic_name = ""
        self.clinic_address = ""
        self.configured = False
        self.revision = 0

    @rx.event
    async def load(self):
        self.is_loading = True
        self.load_failed = False
        self.error_message = ""
        self.success_message = ""
        self.name_error = ""
        self.address_error = ""
        yield
        try:
            token = await self._token()
            with rx.session() as db:
                require_role(db, token, Role.ADMINISTRADOR)
                location = get_clinic_location(db)
            self.clinic_name = location.name
            self.clinic_address = location.address
            self.configured = location.persisted
            self.revision = location.revision
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            self._clear()
            self.load_failed = True
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.load_failed = True
            self.error_message = "Não foi possível carregar as configurações. Tente novamente."
        finally:
            self.is_loading = False
            yield

    @rx.event
    async def save(self, form_data: dict[str, str]):
        if self.is_saving or self.is_loading or self.load_failed:
            return
        self.is_saving = True
        self.error_message = ""
        self.success_message = ""
        self.name_error = ""
        self.address_error = ""
        yield
        try:
            name = str(form_data.get("name", self.clinic_name))
            address = str(form_data.get("address", self.clinic_address))
            token = await self._token()
            with rx.session() as db:
                location = save_clinic_location(
                    db, token=token, name=name, address=address,
                    expected_revision=self.revision,
                )
            self.clinic_name = location.name
            self.clinic_address = location.address
            self.configured = location.persisted
            self.revision = location.revision
            self.success_message = "Configurações atualizadas com sucesso."
        except ClinicSettingsValidationError as exc:
            if exc.field == "name":
                self.name_error = str(exc)
            else:
                self.address_error = str(exc)
        except ClinicSettingsConflictError:
            self.error_message = (
                "As configurações foram modificadas em outra sessão. "
                "Atualize a página antes de tentar salvar novamente."
            )
        except (AuthenticationRequiredError, RoleForbiddenError, PasswordChangeRequiredError) as exc:
            yield rx.redirect("/login" if isinstance(exc, AuthenticationRequiredError) else "/acesso-negado")
        except Exception:
            self.error_message = "Não foi possível salvar as configurações. Tente novamente."
        finally:
            self.is_saving = False
            yield
