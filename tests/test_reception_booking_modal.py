"""Regression tests for the receptionist's in-place booking calendar."""

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus
from vitta_one.appointment_scheduling.state import (
    _masked_booking_contact,
    booking_calendar_cells,
)


def _slot(day: str, status: AvailabilitySlotStatus, slot_id: int) -> dict:
    return {
        "id": slot_id,
        "value": str(slot_id),
        "professional_id": 10,
        "professional_name": "Dra. Exemplo",
        "starts_at": f"{day} às 09:00",
        "date_label": day,
        "time_label": "09:00",
        "status": status.value,
        "status_label": status.label,
    }


def test_calendar_only_enables_persisted_available_slots_within_45_days():
    slots = [
        _slot("05/11/2026", AvailabilitySlotStatus.AVAILABLE, 1),
        _slot("05/11/2026", AvailabilitySlotStatus.BOOKED, 2),
        _slot("06/11/2026", AvailabilitySlotStatus.INACTIVE, 3),
        _slot("20/12/2026", AvailabilitySlotStatus.AVAILABLE, 4),
    ]
    cells = booking_calendar_cells(
        slots, "2026-11", "05/11/2026", "2026-10-31", "2026-12-14"
    )
    by_day = {cell["date_label"]: cell for cell in cells}
    assert by_day["05/11/2026"]["has_slots"] is True
    assert by_day["05/11/2026"]["slot_count"] == 1
    assert by_day["05/11/2026"]["is_selected"] is True
    assert by_day["06/11/2026"]["has_slots"] is False
    assert by_day["01/11/2026"]["has_slots"] is False
    assert all("sem horários" in cell["aria_label"] for cell in cells
               if not cell["has_slots"])


def test_calendar_rejects_slots_beyond_window_and_outside_current_month():
    slots = [
        _slot("15/12/2026", AvailabilitySlotStatus.AVAILABLE, 1),
        _slot("14/12/2026", AvailabilitySlotStatus.AVAILABLE, 2),
    ]
    cells = booking_calendar_cells(
        slots, "2026-12", "", "2026-10-31", "2026-12-14"
    )
    by_day = {cell["date_label"]: cell for cell in cells}
    assert by_day["14/12/2026"]["has_slots"] is True
    assert by_day["15/12/2026"]["has_slots"] is False
    assert not any(cell["has_slots"] for cell in booking_calendar_cells(
        slots, "2026-11", "", "2026-10-31", "2026-12-14"
    ))


def test_booking_search_never_exposes_full_patient_phone():
    assert _masked_booking_contact("(11) 91234-5678") == "Telefone final 5678"
    assert _masked_booking_contact(None) == "Telefone não informado"
    assert _masked_booking_contact("12") == "Telefone não informado"
