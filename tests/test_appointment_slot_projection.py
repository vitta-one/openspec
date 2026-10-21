"""Protect the appointment availability projection used by the receptionist calendar.

Slots represent offered times; consultation timestamps belong to ConsultationItem.
"""
from datetime import datetime, timezone

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus
from vitta_one.appointment_scheduling.service import AvailabilitySlotItem
from vitta_one.appointment_scheduling.state import _slot_rows


def test_available_slot_projection_does_not_access_consultation_fields(
    monkeypatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")
    slot = AvailabilitySlotItem(
        id=42,
        professional_id=9,
        professional_name="Dra. Teste",
        starts_at=datetime(2026, 10, 22, 15, tzinfo=timezone.utc),
        status=AvailabilitySlotStatus.AVAILABLE,
    )

    rows = _slot_rows([slot])

    assert len(rows) == 1
    assert rows[0]["id"] == 42
    assert rows[0]["value"] == "42"
    assert rows[0]["professional_id"] == 9
    assert rows[0]["status"] == AvailabilitySlotStatus.AVAILABLE.value
    assert "confirmed_at" not in rows[0]
    assert "started_at" not in rows[0]
    assert "completed_at" not in rows[0]
