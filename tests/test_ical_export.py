"""Pure iCalendar serialization tests, no database or external provider."""

from datetime import datetime, timezone

import pytest

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.ical_export import build_consultation_ics
from vitta_one.appointment_scheduling.service import ConsultationItem


def consultation(
    *,
    status: ConsultationStatus = ConsultationStatus.AGENDADA,
    doctor_name: str = "Médico da Clínica",
    scheduled_at: datetime | None = None,
) -> ConsultationItem:
    return ConsultationItem(
        id=42,
        patient_id=12,
        patient_name="Paciente Protegido",
        professional_id=5,
        professional_name=doctor_name,
        availability_slot_id=19,
        scheduled_at=scheduled_at or datetime(2026, 11, 3, 14, 30, tzinfo=timezone.utc),
        status=status,
        confirmed_at=None,
        started_at=None,
        completed_at=None,
        cancelled_at=None,
    )


def test_ics_contains_real_utc_start_but_no_patient_or_clinical_details():
    result = build_consultation_ics(
        consultation(),
        now=datetime(2026, 10, 29, 22, 0, tzinfo=timezone.utc),
    )
    assert "BEGIN:VCALENDAR\r\n" in result
    assert "BEGIN:VEVENT\r\n" in result
    assert "DTSTART:20261103T143000Z\r\n" in result
    assert "DTSTAMP:20261029T220000Z" in result
    assert "CLASS:PRIVATE" in result
    assert "Paciente Protegido" not in result
    assert "DTEND" not in result
    assert "Vitta One" in result


def test_ics_escapes_calendar_control_characters():
    result = build_consultation_ics(
        consultation(doctor_name="Dra. Maria; Médico, A\\B"),
    )
    assert "Dra. Maria\\; Médico\\, A\\\\B" in result


def test_ics_rejects_cancelled_appointment():
    with pytest.raises(ValueError, match="canceladas"):
        build_consultation_ics(consultation(status=ConsultationStatus.CANCELADA))


def test_ics_requires_timezone_aware_instant():
    with pytest.raises(ValueError, match="fuso horário"):
        build_consultation_ics(
            consultation(scheduled_at=datetime(2026, 11, 3, 9, 30))
        )
