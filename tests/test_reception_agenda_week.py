"""Focused regression tests for the reception weekly agenda projection."""

from datetime import date, timedelta

import pytest

from vitta_one.appointment_scheduling.reception_calendar import (
    build_week_days,
    filter_consultations_for_day,
    week_bounds,
)


def _consultation(consultation_id, day, time, status="AGENDADA"):
    return {
        "id": consultation_id,
        "scheduled_at": f"{day} às {time}",
        "patient_name": f"Paciente {consultation_id}",
        "professional_name": "Profissional QA",
        "status": status,
        "status_label": status.replace("_", " ").capitalize(),
    }


def test_week_bounds_are_inclusive_and_cross_month_year():
    assert week_bounds("2026-10-31") == ("2026-10-31", "2026-11-06")
    assert week_bounds("2026-12-30") == ("2026-12-30", "2027-01-05")
    with pytest.raises(ValueError):
        week_bounds("2026-02-30")


def test_empty_week_contains_seven_small_zero_count_days():
    days = build_week_days([], "2026-10-31", "", "2026-10-31")
    assert len(days) == 7
    assert [d["date_iso"] for d in days] == [
        (date(2026, 10, 31) + timedelta(days=n)).isoformat() for n in range(7)
    ]
    assert days[0]["is_today"]
    assert not any(day["count"] or day["entries"] for day in days)


def test_calendar_groups_real_consultations_and_keeps_more_count():
    rows = [
        _consultation(3, "31/10/2026", "10:30", "CONFIRMADA"),
        _consultation(1, "31/10/2026", "08:00"),
        _consultation(2, "31/10/2026", "09:00"),
        _consultation(4, "01/11/2026", "08:00", "CANCELADA"),
        _consultation(5, "07/11/2026", "10:00"),
    ]
    days = build_week_days(rows, "2026-10-31", "2026-10-31", "2026-10-31")
    assert days[0]["count"] == 3
    assert [item["id"] for item in days[0]["entries"]] == [1, 2]
    assert days[0]["extra_count"] == 1
    assert days[0]["is_selected"]
    assert days[1]["entries"][0]["status"] == "CANCELADA"
    assert sum(day["count"] for day in days) == 4


def test_selected_day_filters_same_authorized_rows_without_mutating_source():
    rows = [
        _consultation(1, "31/10/2026", "08:00"),
        _consultation(2, "01/11/2026", "08:00"),
    ]
    assert filter_consultations_for_day(rows, "") == rows
    assert [r["id"] for r in filter_consultations_for_day(rows, "2026-11-01")] == [2]
    assert filter_consultations_for_day(rows, "2026-11-02") == []
    assert len(rows) == 2
