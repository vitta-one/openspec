"""Portable, privacy-minimized iCalendar export for one authorized consultation.

No duration, clinical details or clinic address are fabricated. The caller must
first revalidate its authenticated role and the consultation in the database.
"""

from datetime import datetime, timezone

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import ConsultationItem


def _escape_text(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def build_consultation_ics(consultation: ConsultationItem, *, now: datetime | None = None) -> str:
    """Export a start-time-only event that calendar applications can import."""
    if consultation.status == ConsultationStatus.CANCELADA:
        raise ValueError("Consultas canceladas não podem ser adicionadas ao calendário.")
    starts_at = consultation.scheduled_at
    if starts_at.tzinfo is None:
        raise ValueError("Data sem fuso horário definido.")
    start = starts_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    generated = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    stamp = generated.strftime("%Y%m%dT%H%M%SZ")
    summary = _escape_text(f"Consulta médica — {consultation.professional_name}")
    description = _escape_text(
        "Consulta agendada pelo Vitta One. Confirme local e duração com a clínica."
    )
    # No DTEND: appointment length was not provided by the domain.
    # CLASS:PRIVATE prevents unnecessarily revealing the event title in shared calendars.
    return "\r\n".join((
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Vitta One//Agenda de Consultas//PT-BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:vitta-one-consulta-{consultation.id}@local",
        f"DTSTAMP:{stamp}",
        f"DTSTART:{start}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        "STATUS:CONFIRMED",
        "CLASS:PRIVATE",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ))
