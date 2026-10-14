"""Persisted operational metrics; no auth or UI and no clinical contents."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import (
    clinic_date_range_to_utc, clinic_today_iso, ensure_utc,
)
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus


@dataclass(frozen=True)
class NextConsultation:
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
    next_consultations: tuple[NextConsultation, ...]


def _count(db: Session, query) -> int:
    return int(db.exec(query).one())


def get_reception_overview(db: Session, *, now: datetime | None = None) -> ReceptionOverview:
    """Read consistent, explicitly-defined projections from persisted data only.

    Scheduled/confirmed are by local *appointment date*, finished by actual
    queue finish date. Waiting/attending are live stock, regardless of date.
    'Arrivals pending' is not a medical judgment or an automatic no-show.
    """
    current = ensure_utc(now or datetime.now(timezone.utc))
    clinic_date = clinic_today_iso(current)
    start, end = clinic_date_range_to_utc(clinic_date, clinic_date)
    assert start is not None and end is not None

    day_consultations = (
        Consultation.scheduled_at >= start,
        Consultation.scheduled_at < end,
    )
    scheduled_today = _count(
        db, select(func.count(Consultation.id)).where(
            *day_consultations, Consultation.status != ConsultationStatus.CANCELADA.value
        ),
    )
    confirmed_today = _count(
        db, select(func.count(Consultation.id)).where(
            *day_consultations, Consultation.status == ConsultationStatus.CONFIRMADA.value
        ),
    )
    arrivals_pending = _count(
        db, select(func.count(Consultation.id)).where(
            *day_consultations,
            Consultation.status == ConsultationStatus.AGENDADA.value,
            Consultation.scheduled_at < current,
        ),
    )
    waiting = _count(
        db, select(func.count(QueueEntry.id)).where(
            QueueEntry.status == QueueStatus.AGUARDANDO.value
        ),
    )
    attending = _count(
        db, select(func.count(QueueEntry.id)).where(
            QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value
        ),
    )
    finished_today = _count(
        db, select(func.count(QueueEntry.id)).where(
            QueueEntry.status == QueueStatus.FINALIZADO.value,
            QueueEntry.finished_at >= start, QueueEntry.finished_at < end,
        ),
    )

    def waiting_in(priority: QueuePriority) -> int:
        return _count(db, select(func.count(QueueEntry.id)).where(
            QueueEntry.status == QueueStatus.AGUARDANDO.value,
            QueueEntry.priority == priority.value,
        ))

    rows = db.exec(
        select(Consultation, Patient, Professional)
        .join(Patient, Patient.id == Consultation.patient_id)
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(
            Consultation.status == ConsultationStatus.AGENDADA.value,
            Consultation.scheduled_at >= current,
        )
        .order_by(Consultation.scheduled_at, Consultation.id)
        .limit(5)
    ).all()
    upcoming = tuple(
        NextConsultation(
            id=consultation.id,
            patient_name=patient.name,
            professional_name=professional.name,
            scheduled_at=ensure_utc(consultation.scheduled_at),
        )
        for consultation, patient, professional in rows
    )
    return ReceptionOverview(
        as_of=current, clinic_date=clinic_date,
        scheduled_today=scheduled_today, waiting=waiting, attending=attending,
        finished_today=finished_today, confirmed_today=confirmed_today,
        arrivals_pending=arrivals_pending,
        waiting_red=waiting_in(QueuePriority.VERMELHO),
        waiting_yellow=waiting_in(QueuePriority.AMARELO),
        waiting_green=waiting_in(QueuePriority.VERDE),
        next_consultations=upcoming,
    )
