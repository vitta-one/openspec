"""Usability regression checks for daily scheduling presentation."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus
from vitta_one.appointment_scheduling.state import _slot_rows, group_slots_by_day


def _slot(slot_id: int, day: int, hour: int, doctor: str, status=AvailabilitySlotStatus.AVAILABLE):
    return SimpleNamespace(
        id=slot_id,
        professional_id=slot_id,
        professional_name=doctor,
        starts_at=datetime(2026, 10, day, hour, 0, tzinfo=timezone.utc),
        status=status,
        confirmed_at=None,
        started_at=None,
        completed_at=None,
    )


def test_slots_grouped_by_real_local_day_and_keep_professional_and_status(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")
    slots = _slot_rows([
        _slot(1, 16, 12, "Dra. A"),
        _slot(2, 16, 13, "Dr. B", AvailabilitySlotStatus.BOOKED),
        _slot(3, 17, 12, "Dra. A"),
    ])
    days = group_slots_by_day(slots)
    assert [group["date_label"] for group in days] == ["16/10/2026", "17/10/2026"]
    assert [item["time_label"] for item in days[0]["slots"]] == ["09:00", "10:00"]
    assert [item["professional_name"] for item in days[0]["slots"]] == ["Dra. A", "Dr. B"]
    assert days[0]["slots"][1]["status"] == AvailabilitySlotStatus.BOOKED.value
    assert slots[0]["starts_at"] == "16/10/2026 às 09:00"


def test_group_empty_slots_returns_no_fake_dates():
    assert group_slots_by_day([]) == []


def test_same_day_different_times_not_merged_as_one_slot(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")
    slots = _slot_rows([
        _slot(1, 16, 12, "Dra. A"),
        _slot(2, 16, 12, "Dr. B"),
        _slot(3, 16, 14, "Dra. A"),
    ])
    group = group_slots_by_day(slots)
    assert len(group) == 1
    assert len(group[0]["slots"]) == 3
    assert [item["id"] for item in group[0]["slots"]] == [1, 2, 3]
