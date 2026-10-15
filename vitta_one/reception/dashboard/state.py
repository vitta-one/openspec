"""Reflex state for a securely loaded reception dashboard."""
from datetime import date, timedelta

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
from vitta_one.reception.dashboard.application import reception_overview
from vitta_one.reception.dashboard.service import ReceptionOverview


_WEEKDAY_SHORT = ("seg", "ter", "qua", "qui", "sex", "sáb", "dom")
_WEEKDAY_LONG = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


def _calendar_projection(snapshot: ReceptionOverview) -> tuple[
    list[dict[str, str]], list[dict[str, str]], str
]:
    zone = clinic_timezone()
    events: list[dict[str, str]] = []
    counts: dict[str, dict[str, int]] = {}

    for item in snapshot.calendar_consultations:
        local_time = item.scheduled_at.astimezone(zone)
        day_iso = local_time.date().isoformat()
        day_counts = counts.setdefault(day_iso, {"active": 0, "cancelled": 0})
        if item.status is ConsultationStatus.CANCELADA:
            day_counts["cancelled"] += 1
            status_label = item.status.label
        else:
            day_counts["active"] += 1
            status_label = item.status.label

        is_pending = (
            item.status is ConsultationStatus.AGENDADA
            and day_iso == snapshot.clinic_date
            and item.scheduled_at < snapshot.as_of
        )
        if is_pending:
            status_label = "Chegada pendente"

        events.append(
            {
                "date": day_iso,
                "time": local_time.strftime("%H:%M"),
                "patient": item.patient_name,
                "professional": item.professional_name,
                "status": status_label,
                "status_value": item.status.value,
                "is_pending": "true" if is_pending else "false",
            }
        )

    first_day = date.fromisoformat(snapshot.clinic_date)
    days: list[dict[str, str]] = []
    for offset in range(7):
        day = first_day + timedelta(days=offset)
        day_iso = day.isoformat()
        weekday_index = day.weekday()
        day_counts = counts.get(day_iso, {"active": 0, "cancelled": 0})
        active_count = day_counts["active"]
        cancelled_count = day_counts["cancelled"]
        active_label = (
            (
                "0 consultas não canceladas"
                if cancelled_count
                else "Sem consultas"
            )
            if active_count == 0
            else f"{active_count} consulta" + ("" if active_count == 1 else "s")
        )
        cancelled_label = (
            f"{cancelled_count} cancelada"
            + ("" if cancelled_count == 1 else "s")
            if cancelled_count
            else ""
        )
        details = [active_label]
        if cancelled_label:
            details.append(cancelled_label)
        date_display = day.strftime("%d/%m")
        is_today = day_iso == snapshot.clinic_date
        days.append(
            {
                "date": day_iso,
                "date_display": date_display,
                "day_number": str(day.day),
                "weekday": _WEEKDAY_SHORT[weekday_index],
                "weekday_long": _WEEKDAY_LONG[weekday_index],
                "weekday_label": (
                    f"Hoje · {_WEEKDAY_SHORT[weekday_index]}"
                    if is_today
                    else _WEEKDAY_SHORT[weekday_index]
                ),
                "count_label": (
                    f"{active_count} consulta"
                    + ("" if active_count == 1 else "s")
                ),
                "cancelled_label": cancelled_label,
                "summary": " · ".join(details),
                "is_today": "true" if is_today else "false",
                "aria_label": (
                    f"Mostrar agenda de {_WEEKDAY_LONG[weekday_index]}, "
                    f"{date_display}: {'; '.join(details)}"
                ),
            }
        )

    last_day = first_day + timedelta(days=6)
    range_label = f"{first_day.strftime('%d/%m')} – {last_day.strftime('%d/%m')}"
    return events, days, range_label


class ReceptionDashboardState(rx.State):
    scheduled_today: int = 0
    waiting: int = 0
    attending: int = 0
    finished_today: int = 0
    confirmed_today: int = 0
    arrivals_pending: int = 0
    waiting_red: int = 0
    waiting_yellow: int = 0
    waiting_green: int = 0
    calendar_consultations: list[dict[str, str]] = []
    calendar_days: list[dict[str, str]] = []
    selected_calendar_date: str = ""
    calendar_range: str = ""
    pending_arrivals: list[dict[str, str]] = []
    clinic_day: str = ""
    last_updated: str = ""
    has_loaded: bool = False
    is_loading: bool = False
    error_message: str = ""

    @rx.var
    def selected_calendar_consultations(self) -> list[dict[str, str]]:
        return [
            item
            for item in self.calendar_consultations
            if item["date"] == self.selected_calendar_date
        ]

    @rx.var
    def selected_calendar_label(self) -> str:
        for day in self.calendar_days:
            if day["date"] == self.selected_calendar_date:
                prefix = "Hoje, " if day["is_today"] == "true" else ""
                return f"{prefix}{day['weekday_long']}, {day['date_display']}"
        return ""

    @rx.var
    def selected_calendar_summary(self) -> str:
        for day in self.calendar_days:
            if day["date"] == self.selected_calendar_date:
                return day["summary"]
        return ""

    def _clear_data(self) -> None:
        self.scheduled_today = 0
        self.waiting = 0
        self.attending = 0
        self.finished_today = 0
        self.confirmed_today = 0
        self.arrivals_pending = 0
        self.waiting_red = 0
        self.waiting_yellow = 0
        self.waiting_green = 0
        self.calendar_consultations = []
        self.calendar_days = []
        self.selected_calendar_date = ""
        self.calendar_range = ""
        self.pending_arrivals = []
        self.clinic_day = ""
        self.last_updated = ""
        self.has_loaded = False

    @rx.event
    def select_calendar_day(self, date_value: str) -> None:
        if any(day["date"] == date_value for day in self.calendar_days):
            self.selected_calendar_date = date_value

    @rx.event
    async def load(self):
        """Every refresh revalidates the session and role before reading data."""
        previous_date = self.selected_calendar_date
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            auth = await self.get_state(AuthState)
            with rx.session() as db:
                snapshot = reception_overview(db, token=auth.session_token)

            self.scheduled_today = snapshot.scheduled_today
            self.waiting = snapshot.waiting
            self.attending = snapshot.attending
            self.finished_today = snapshot.finished_today
            self.confirmed_today = snapshot.confirmed_today
            self.arrivals_pending = snapshot.arrivals_pending
            self.waiting_red = snapshot.waiting_red
            self.waiting_yellow = snapshot.waiting_yellow
            self.waiting_green = snapshot.waiting_green
            events, days, calendar_range = _calendar_projection(snapshot)
            self.calendar_consultations = events
            self.calendar_days = days
            self.calendar_range = calendar_range
            available_dates = {day["date"] for day in days}
            self.selected_calendar_date = (
                previous_date
                if previous_date in available_dates
                else snapshot.clinic_date
            )
            self.pending_arrivals = [
                {
                    "id": str(item.id),
                    "patient": item.patient_name,
                    "professional": item.professional_name,
                    "when": format_clinic_datetime(item.scheduled_at),
                }
                for item in snapshot.pending_arrivals
            ]
            day = date.fromisoformat(snapshot.clinic_date)
            self.clinic_day = day.strftime("%d/%m/%Y")
            self.last_updated = format_clinic_datetime(snapshot.as_of)
            self.has_loaded = True
        except (AuthenticationRequiredError, PasswordChangeRequiredError):
            self._clear_data()
            yield rx.redirect("/login")
        except RoleForbiddenError:
            self._clear_data()
            yield rx.redirect("/acesso-negado")
        except Exception:
            self._clear_data()
            self.error_message = (
                "Não foi possível atualizar o painel agora. Tente novamente."
            )
        finally:
            self.is_loading = False
            yield
