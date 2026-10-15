"""Persisted operational metrics; no auth or UI and no clinical contents."""
from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import func, or_
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    ProfessionalOption,
    list_active_professionals,
)
from vitta_one.appointment_scheduling.temporal import (
    clinic_date_after_iso,
    clinic_date_range_to_utc,
    clinic_today_iso,
    ensure_utc,
)
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import (
    Professional,
    ProfessionalSpecialty,
    Specialty,
)
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus


@dataclass(frozen=True)
class CalendarConsultation:
    id: int
    patient_name: str
    professional_name: str
    scheduled_at: datetime
    status: ConsultationStatus


@dataclass(frozen=True)
class PendingArrival:
    id: int
    patient_name: str
    professional_name: str
    scheduled_at: datetime


@dataclass(frozen=True)
class ReceptionOverview:
    as_of: datetime
    clinic_date: str
    scheduled_today: int
    waiting: int
    attending: int
    finished_today: int
    confirmed_today: int
    arrivals_pending: int
    waiting_red: int
    waiting_yellow: int
    waiting_green: int
    calendar_consultations: tuple[CalendarConsultation, ...]
    pending_arrivals: tuple[PendingArrival, ...]


def get_reception_overview(
    db: Session, *, now: datetime | None = None
) -> ReceptionOverview:
    """Read consistent, explicitly-defined projections from persisted data only.

    Scheduled/confirmed are by local appointment date, finished by actual
    queue finish date. Waiting/attending are live stock, regardless of date.
    The calendar covers seven clinic-local dates from today. 'Arrivals pending'
    is not a medical judgment or an automatic no-show.
    """
    current = ensure_utc(now or datetime.now(timezone.utc))
    clinic_date = clinic_today_iso(current)
    start, end = clinic_date_range_to_utc(clinic_date, clinic_date)
    assert start is not None and end is not None

    day_consultations = (
        Consultation.scheduled_at >= start,
        Consultation.scheduled_at < end,
    )

    consultation_counts = db.exec(
        select(
            func.count(Consultation.id)
            .filter(Consultation.status != ConsultationStatus.CANCELADA.value),
            func.count(Consultation.id)
            .filter(Consultation.status == ConsultationStatus.CONFIRMADA.value),
            func.count(Consultation.id).filter(
                Consultation.status == ConsultationStatus.AGENDADA.value,
                Consultation.scheduled_at < current,
            ),
        ).where(*day_consultations)
    ).one()
    scheduled_today, confirmed_today, arrivals_pending = (
        int(value or 0) for value in consultation_counts
    )

    queue_counts = db.exec(
        select(
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.AGUARDANDO.value
            ),
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value
            ),
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.FINALIZADO.value,
                QueueEntry.finished_at >= start,
                QueueEntry.finished_at < end,
            ),
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.AGUARDANDO.value,
                QueueEntry.priority == QueuePriority.VERMELHO.value,
            ),
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.AGUARDANDO.value,
                QueueEntry.priority == QueuePriority.AMARELO.value,
            ),
            func.count(QueueEntry.id).filter(
                QueueEntry.status == QueueStatus.AGUARDANDO.value,
                QueueEntry.priority == QueuePriority.VERDE.value,
            ),
        )
    ).one()
    waiting, attending, finished_today, waiting_red, waiting_yellow, waiting_green = (
        int(value or 0) for value in queue_counts
    )

    calendar_end_date = clinic_date_after_iso(6, current)
    calendar_start, calendar_end = clinic_date_range_to_utc(
        clinic_date, calendar_end_date
    )
    assert calendar_start is not None and calendar_end is not None
    calendar_rows = db.exec(
        select(Consultation, Patient, Professional)
        .join(Patient, Patient.id == Consultation.patient_id)
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(
            Consultation.scheduled_at >= calendar_start,
            Consultation.scheduled_at < calendar_end,
        )
        .order_by(Consultation.scheduled_at, Consultation.id)
    ).all()
    calendar_consultations = tuple(
        CalendarConsultation(
            id=consultation.id,
            patient_name=patient.name,
            professional_name=professional.name,
            scheduled_at=ensure_utc(consultation.scheduled_at),
            status=ConsultationStatus(consultation.status),
        )
        for consultation, patient, professional in calendar_rows
        if consultation.id is not None
    )

    pending_rows = db.exec(
        select(Consultation, Patient, Professional)
        .join(Patient, Patient.id == Consultation.patient_id)
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(
            *day_consultations,
            Consultation.status == ConsultationStatus.AGENDADA.value,
            Consultation.scheduled_at < current,
        )
        .order_by(Consultation.scheduled_at, Consultation.id)
        .limit(5)
    ).all()
    pending = tuple(
        PendingArrival(
            id=consultation.id,
            patient_name=patient.name,
            professional_name=professional.name,
            scheduled_at=ensure_utc(consultation.scheduled_at),
        )
        for consultation, patient, professional in pending_rows
        if consultation.id is not None
    )

    return ReceptionOverview(
        as_of=current,
        clinic_date=clinic_date,
        scheduled_today=scheduled_today,
        waiting=waiting,
        attending=attending,
        finished_today=finished_today,
        confirmed_today=confirmed_today,
        arrivals_pending=arrivals_pending,
        waiting_red=waiting_red,
        waiting_yellow=waiting_yellow,
        waiting_green=waiting_green,
        calendar_consultations=calendar_consultations,
        pending_arrivals=pending,
    )


@dataclass(frozen=True)
class ReceptionDayAppointment:
    """A privacy-minimal row for the receptionist's daily consultation table."""

    id: int
    patient_name: str
    patient_phone: str | None
    professional_name: str
    specialty_names: tuple[str, ...]
    scheduled_at: datetime
    status: ConsultationStatus


@dataclass(frozen=True)
class ReceptionDaySnapshot:
    """Server-paginated daily operations and active professional filter options."""

    as_of: datetime
    clinic_date: str
    appointments: tuple[ReceptionDayAppointment, ...]
    professionals: tuple[ProfessionalOption, ...]
    page: int
    page_size: int
    total: int
    total_pages: int


def _day_search_clause(value: str):
    """Build a bounded literal search across appointment patient identity fields."""
    query = " ".join(str(value or "").split())[:100]
    if not query:
        return None

    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    clauses = [Patient.name.ilike(f"%{escaped}%", escape="\\")]
    digits = re.sub(r"\D", "", query)
    if digits:
        clauses.extend(
            (
                Patient.cpf.like(f"%{digits}%"),
                func.coalesce(Patient.phone, "").like(f"%{digits}%"),
            )
        )
    return or_(*clauses)


def get_reception_day(
    db: Session,
    *,
    now: datetime | None = None,
    professional_id: int | None = None,
    search: str = "",
    page: int = 1,
    page_size: int = 7,
) -> ReceptionDaySnapshot:
    """Return a real, clinic-local day view with SQL filters and bounded pages.

    Cancelled consultations remain visible so the receptionist can understand
    the day's full record. No clinical record, symptom, diagnosis, or priority
    is read or returned by this projection.
    """
    if isinstance(page, bool) or page < 1:
        page = 1
    if isinstance(page_size, bool) or page_size < 1 or page_size > 50:
        raise ValueError("O tamanho da página está fora do limite permitido.")
    if professional_id is not None:
        if isinstance(professional_id, bool) or professional_id < 1:
            raise ValueError("Selecione um profissional válido.")
        if db.get(Professional, professional_id) is None:
            raise ValueError("Selecione um profissional válido.")

    current = ensure_utc(now or datetime.now(timezone.utc))
    clinic_date = clinic_today_iso(current)
    start, end = clinic_date_range_to_utc(clinic_date, clinic_date)
    assert start is not None and end is not None

    conditions = [
        Consultation.scheduled_at >= start,
        Consultation.scheduled_at < end,
    ]
    if professional_id is not None:
        conditions.append(Consultation.professional_id == professional_id)
    search_clause = _day_search_clause(search)
    if search_clause is not None:
        conditions.append(search_clause)

    total = int(
        db.exec(
            select(func.count(Consultation.id))
            .select_from(Consultation)
            .join(Patient, Patient.id == Consultation.patient_id)
            .where(*conditions)
        ).one()
        or 0
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = min(page, total_pages)

    rows = db.exec(
        select(Consultation, Patient, Professional)
        .join(Patient, Patient.id == Consultation.patient_id)
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(*conditions)
        .order_by(Consultation.scheduled_at, Consultation.id)
        .offset((current_page - 1) * page_size)
        .limit(page_size)
    ).all()
    professional_ids = {
        professional.id
        for _, _, professional in rows
        if professional.id is not None
    }
    specialties_by_professional: dict[int, list[str]] = {}
    if professional_ids:
        specialty_rows = db.exec(
            select(ProfessionalSpecialty.professional_id, Specialty.name)
            .join(Specialty, Specialty.id == ProfessionalSpecialty.specialty_id)
            .where(
                ProfessionalSpecialty.professional_id.in_(professional_ids),
                Specialty.is_active.is_(True),
            )
            .order_by(
                ProfessionalSpecialty.professional_id,
                Specialty.normalized_name,
                Specialty.id,
            )
        ).all()
        for professional_id_value, specialty_label in specialty_rows:
            specialties_by_professional.setdefault(
                professional_id_value, []
            ).append(specialty_label)

    appointments = tuple(
        ReceptionDayAppointment(
            id=consultation.id,
            patient_name=patient.name,
            patient_phone=patient.phone,
            professional_name=professional.name,
            specialty_names=tuple(
                specialties_by_professional.get(professional.id, ())
            ),
            scheduled_at=ensure_utc(consultation.scheduled_at),
            status=ConsultationStatus(consultation.status),
        )
        for consultation, patient, professional in rows
        if consultation.id is not None and professional.id is not None
    )

    return ReceptionDaySnapshot(
        as_of=current,
        clinic_date=clinic_date,
        appointments=appointments,
        professionals=tuple(list_active_professionals(db)),
        page=current_page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
