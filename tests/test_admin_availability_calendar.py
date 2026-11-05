"""Regression checks for the administrator's real monthly availability view."""

from types import SimpleNamespace

from vitta_one.appointment_scheduling.state import (
    _professional_rows,
    build_admin_calendar_cells,
)


def test_professionals_show_names_without_internal_registration():
    doctors = [
        SimpleNamespace(id=11, name="Dra. Helena", registration_identifier="INT-67B597B85AA04E34A48C811B7B4EE59F"),
        SimpleNamespace(id=12, name="Dr. Bruno", registration_identifier="CRM-SP 12345"),
    ]
    rows = _professional_rows(doctors)
    assert [row["label"] for row in rows] == ["Dra. Helena", "Dr. Bruno"]
    assert [row["value"] for row in rows] == ["11", "12"]


def test_professionals_with_duplicate_names_are_distinguishable():
    doctors = [
        SimpleNamespace(id=11, name="Dra. Helena", registration_identifier="CRM-SP 12345"),
        SimpleNamespace(id=12, name="Dra. Helena", registration_identifier="INT-12345"),
    ]
    rows = _professional_rows(doctors)
    assert rows[0]["label"] == "Dra. Helena · CRM-SP 12345"
    assert rows[1]["label"] == "Dra. Helena · cadastro 12"


def test_calendar_days_have_only_persisted_counts():
    slots = [
        {"date_label": "02/11/2026"},
        {"date_label": "02/11/2026"},
        {"date_label": "04/11/2026"},
    ]
    days = build_admin_calendar_cells(slots, "2026-11", "03/11/2026")
    monday = next(day for day in days if day["date_label"] == "02/11/2026")
    tuesday = next(day for day in days if day["date_label"] == "03/11/2026")
    assert monday["slot_count"] == 2
    assert monday["has_slots"] is True
    assert tuesday["has_slots"] is False
    assert tuesday["is_selected"] is True
    assert "sem horários" in tuesday["aria_label"]


def test_calendar_does_not_activate_other_months():
    days = build_admin_calendar_cells([], "2026-11", "")
    adjacent = [day for day in days if not day["is_current_month"]]
    assert adjacent
    assert all(not day["has_slots"] for day in adjacent)
    assert build_admin_calendar_cells([], "invalid", "") == []
