"""Clinic-local seven-day reception agenda projection (display only)."""

from datetime import date, datetime, timedelta
from typing import Any, Mapping, Sequence, TypedDict


_WEEKDAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
_MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


class AgendaWeekEntry(TypedDict):
    id: int
    time: str
    patient_name: str
    professional_name: str
    status: str
    status_label: str


class AgendaWeekDay(TypedDict):
    date_iso: str
    date_label: str
    day_number_label: str
    day_label: str
    is_today: bool
    is_selected: bool
    count: int
    entries: list[AgendaWeekEntry]
    extra_count: int
    aria_label: str


class AgendaCalendarAppointment(TypedDict):
    date_iso: str
    time: str
    patient_name: str
    professional_name: str
    status: str
    status_label: str


class AgendaCalendarCell(TypedDict):
    date_iso: str
    appointments: list[AgendaCalendarAppointment]
    appointment_count: int
    display_appointment: AgendaCalendarAppointment
    extra_count: int


class AgendaCalendarHourRow(TypedDict):
    time_label: str
    cells: list[AgendaCalendarCell]


def week_bounds(start_iso: str) -> tuple[str, str]:
    """Seven inclusive clinic-local dates; never use browser timezone here."""
    first = date.fromisoformat(start_iso)
    return first.isoformat(), (first + timedelta(days=6)).isoformat()


def format_week_period_label(start_iso: str) -> str:
    """Format a seven-day range in the approved Portuguese calendar style."""
    first_iso, last_iso = week_bounds(start_iso)
    first = date.fromisoformat(first_iso)
    last = date.fromisoformat(last_iso)
    if first.year == last.year and first.month == last.month:
        return f"{first.day}–{last.day} de {_MONTHS[last.month - 1]} de {last.year}"
    if first.year == last.year:
        return (
            f"{first.day} de {_MONTHS[first.month - 1]}–"
            f"{last.day} de {_MONTHS[last.month - 1]} de {last.year}"
        )
    return (
        f"{first.day} de {_MONTHS[first.month - 1]} de {first.year}–"
        f"{last.day} de {_MONTHS[last.month - 1]} de {last.year}"
    )


def monday_of_week(day_iso: str) -> str:
    """Return the clinic-local Monday containing a selected date."""
    selected = date.fromisoformat(day_iso)
    return (selected - timedelta(days=selected.weekday())).isoformat()


def filter_consultations_for_day(
    consultations: Sequence[dict[str, Any]], selected_iso: str
) -> list[dict[str, Any]]:
    """Use the same authorized result set as the calendar and table."""
    if not selected_iso:
        return list(consultations)
    selected_label = date.fromisoformat(selected_iso).strftime("%d/%m/%Y às ")
    return [
        row for row in consultations
        if row["scheduled_at"].startswith(selected_label)
    ]


def build_week_days(
    consultations: Sequence[Mapping[str, Any]],
    start_iso: str,
    selected_iso: str,
    today_iso: str,
) -> list[AgendaWeekDay]:
    """Project only persisted consultations. Never generate fictitious slots."""
    first = date.fromisoformat(start_iso)
    by_day: dict[str, list[AgendaWeekEntry]] = {}
    for row in consultations:
        scheduled = datetime.strptime(row["scheduled_at"], "%d/%m/%Y às %H:%M")
        by_day.setdefault(scheduled.date().isoformat(), []).append(
            {
                "id": row["id"],
                "time": scheduled.strftime("%H:%M"),
                "patient_name": row["patient_name"],
                "professional_name": row["professional_name"],
                "status": row["status"],
                "status_label": row["status_label"],
            }
        )

    days: list[AgendaWeekDay] = []
    for offset in range(7):
        day = first + timedelta(days=offset)
        key = day.isoformat()
        entries = sorted(by_day.get(key, []), key=lambda item: (item["time"], item["id"]))
        count = len(entries)
        days.append(
            {
                "date_iso": key,
                "date_label": day.strftime("%d/%m"),
                "day_number_label": str(day.day),
                "day_label": _WEEKDAYS[day.weekday()],
                "is_today": key == today_iso,
                "is_selected": key == selected_iso,
                "count": count,
                "entries": entries[:2],
                "extra_count": max(0, count - 2),
                "aria_label": (
                    f"{day:%d/%m/%Y}: {count} consulta(s). "
                    "Selecionar ou remover filtro desta data."
                ),
            }
        )
    return days


def build_calendar_hour_rows(
    consultations: Sequence[Mapping[str, Any]], start_iso: str,
    day_iso: str | None = None,
) -> list[AgendaCalendarHourRow]:
    """Lay out only authorized persisted appointments in a seven-day time grid."""
    first = date.fromisoformat(start_iso)
    last = first + timedelta(days=6)
    by_day_and_hour: dict[str, dict[int, list[AgendaCalendarAppointment]]] = {}
    visible_hours = set(range(7, 19))

    for row in consultations:
        scheduled = datetime.strptime(row["scheduled_at"], "%d/%m/%Y às %H:%M")
        if not first <= scheduled.date() <= last:
            continue
        date_iso = scheduled.date().isoformat()
        hour = scheduled.hour
        if hour not in visible_hours:
            continue
        by_day_and_hour.setdefault(date_iso, {}).setdefault(hour, []).append(
            {
                "date_iso": date_iso,
                "time": scheduled.strftime("%H:%M"),
                "patient_name": str(row["patient_name"]),
                "professional_name": str(row["professional_name"]),
                "status": str(row["status"]),
                "status_label": str(row["status_label"]),
            }
        )

    days = (
        [day_iso]
        if day_iso is not None and first <= date.fromisoformat(day_iso) <= last
        else [(first + timedelta(days=offset)).isoformat() for offset in range(7)]
    )
    hours = list(range(7, 19))
    return [
        {
            "time_label": f"{hour:02d}:00",
            "cells": [
                _calendar_cell(day_iso, by_day_and_hour.get(day_iso, {}).get(hour, []))
                for day_iso in days
            ],
        }
        for hour in hours
    ]


def count_calendar_outside_business_hours(
    consultations: Sequence[Mapping[str, Any]],
    start_iso: str,
    day_iso: str | None = None,
) -> int:
    """Count real appointments shown in the adjacent table, outside grid hours."""
    first = date.fromisoformat(start_iso)
    last = first + timedelta(days=6)
    count = 0
    for row in consultations:
        scheduled = datetime.strptime(row["scheduled_at"], "%d/%m/%Y às %H:%M")
        if not first <= scheduled.date() <= last:
            continue
        if day_iso is not None and scheduled.date().isoformat() != day_iso:
            continue
        if scheduled.hour not in range(7, 19):
            count += 1
    return count


def _calendar_cell(
    date_iso: str, appointments: list[AgendaCalendarAppointment]
) -> AgendaCalendarCell:
    ordered = sorted(appointments, key=lambda item: (item["time"], item["patient_name"]))
    return {
        "date_iso": date_iso,
        "appointments": ordered,
        "appointment_count": len(ordered),
        "display_appointment": ordered[0] if ordered else {
            "date_iso": date_iso,
            "time": "",
            "patient_name": "",
            "professional_name": "",
            "status": "",
            "status_label": "",
        },
        "extra_count": max(0, len(ordered) - 1),
    }
