"""Focused regression tests for the reception weekly agenda projection."""

from datetime import date, timedelta

import pytest

from vitta_one.appointment_scheduling.reception_calendar import (
    build_calendar_hour_rows,
    build_week_days,
    count_calendar_outside_business_hours,
    filter_consultations_for_day,
    format_week_period_label,
    monday_of_week,
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


def test_monday_of_week_aligns_any_day_without_using_browser_timezone():
    assert monday_of_week("2026-11-17") == "2026-11-16"
    assert monday_of_week("2026-11-22") == "2026-11-16"
    assert monday_of_week("2026-11-23") == "2026-11-23"


def test_week_period_label_matches_portuguese_calendar_range():
    assert format_week_period_label("2026-11-16") == "16–22 de novembro de 2026"
    assert format_week_period_label("2026-11-30") == "30 de novembro–6 de dezembro de 2026"
    assert format_week_period_label("2026-12-28") == "28 de dezembro de 2026–3 de janeiro de 2027"


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
    assert days[0]["day_number_label"] == "31"
    assert days[0]["day_label"] == "Sáb"
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


def test_hour_grid_places_real_appointments_in_their_local_day_and_time():
    rows = [
        _consultation(3, "17/11/2026", "08:30", "CONFIRMADA"),
        _consultation(1, "16/11/2026", "09:00", "EM_ANDAMENTO"),
        _consultation(2, "22/11/2026", "20:15", "AGENDADA"),
        _consultation(4, "23/11/2026", "10:00"),
    ]

    grid = build_calendar_hour_rows(rows, "2026-11-16")

    assert grid[0]["time_label"] == "07:00"
    row_by_hour = {row["time_label"]: row for row in grid}
    assert row_by_hour["09:00"]["cells"][0]["appointments"][0]["status"] == "EM_ANDAMENTO"
    assert row_by_hour["08:00"]["cells"][1]["appointments"][0]["time"] == "08:30"
    assert count_calendar_outside_business_hours(rows, "2026-11-16") == 1
    assert not any(
        appointment["patient_name"] == "Paciente 4"
        for row in grid
        for cell in row["cells"]
        for appointment in cell["appointments"]
    )


def test_empty_hour_grid_keeps_reference_business_hours_without_fake_appointments():
    grid = build_calendar_hour_rows([], "2026-11-16")

    assert [row["time_label"] for row in grid] == [f"{hour:02d}:00" for hour in range(7, 19)]
    assert all(not cell["appointments"] for row in grid for cell in row["cells"])


def test_daily_hour_grid_contains_only_the_selected_day():
    rows = [
        _consultation(1, "16/11/2026", "09:00"),
        _consultation(2, "17/11/2026", "10:00"),
    ]
    grid = build_calendar_hour_rows(rows, "2026-11-16", "2026-11-17")
    assert all(len(row["cells"]) == 1 for row in grid)
    assert grid[3]["cells"][0]["appointments"][0]["patient_name"] == "Paciente 2"
    assert count_calendar_outside_business_hours(rows, "2026-11-16", "2026-11-17") == 0
