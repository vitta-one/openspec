"""Clinic-local seven-day reception agenda projection (display only)."""

from datetime import date, datetime, timedelta
from typing import Any, Mapping, Sequence, TypedDict


_WEEKDAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")


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
    day_label: str
    is_today: bool
    is_selected: bool
    count: int
    entries: list[AgendaWeekEntry]
    extra_count: int
    aria_label: str


def week_bounds(start_iso: str) -> tuple[str, str]:
    """Seven inclusive clinic-local dates; never use browser timezone here."""
    first = date.fromisoformat(start_iso)
    return first.isoformat(), (first + timedelta(days=6)).isoformat()


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
