"""Patient-facing appointment discovery over the shared clinic scheduling ledger.

Only public directory attributes and available slots are returned. No other
patient identities, bookings, contact details or prescriptions are queried.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus
from vitta_one.appointment_scheduling.service import SchedulingValidationError
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.models.appointment import ProfessionalAvailabilitySlot
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty


BOOKING_HORIZON_DAYS = 45


@dataclass(frozen=True, slots=True)
class BookableSpecialty:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class BookableDoctor:
    id: int
    name: str
    registration_identifier: str


@dataclass(frozen=True, slots=True)
class BookableSlot:
    id: int
    professional_id: int
    starts_at: datetime


def _now(value: datetime | None = None) -> datetime:
    return ensure_utc(value or datetime.now(timezone.utc))


def list_patient_specialties(db: Session) -> tuple[BookableSpecialty, ...]:
    """Only active specialties currently attached to active professionals."""
    items = db.exec(
        select(Specialty)
        .join(ProfessionalSpecialty, ProfessionalSpecialty.specialty_id == Specialty.id)
        .join(Professional, Professional.id == ProfessionalSpecialty.professional_id)
        .where(Specialty.is_active.is_(True), Professional.is_active.is_(True))
        .distinct()
        .order_by(Specialty.name, Specialty.id)
    ).all()
    return tuple(BookableSpecialty(id=row.id, name=row.name) for row in items)


def list_patient_doctors(
    db: Session, *, specialty_id: int
) -> tuple[BookableDoctor, ...]:
    if specialty_id <= 0:
        return ()
    rows = db.exec(
        select(Professional)
        .join(ProfessionalSpecialty, ProfessionalSpecialty.professional_id == Professional.id)
        .join(Specialty, Specialty.id == ProfessionalSpecialty.specialty_id)
        .where(
            Specialty.id == specialty_id,
            Specialty.is_active.is_(True),
            Professional.is_active.is_(True),
        )
        .distinct()
        .order_by(Professional.name, Professional.id)
    ).all()
    return tuple(
        BookableDoctor(
            id=doctor.id, name=doctor.name,
            registration_identifier=doctor.registration_identifier
        ) for doctor in rows
    )


def list_patient_slots(
    db: Session, *, specialty_id: int, professional_id: int,
    now: datetime | None = None,
) -> tuple[BookableSlot, ...]:
    if specialty_id <= 0 or professional_id <= 0:
        return ()
    timestamp = _now(now)
    rows = db.exec(
        select(ProfessionalAvailabilitySlot)
        .join(
            Professional,
            Professional.id == ProfessionalAvailabilitySlot.professional_id,
        )
        .join(
            ProfessionalSpecialty,
            ProfessionalSpecialty.professional_id == Professional.id,
        )
        .join(Specialty, Specialty.id == ProfessionalSpecialty.specialty_id)
        .where(
            Professional.id == professional_id,
            Professional.is_active.is_(True),
            Specialty.id == specialty_id,
            Specialty.is_active.is_(True),
            ProfessionalAvailabilitySlot.status == AvailabilitySlotStatus.AVAILABLE.value,
            ProfessionalAvailabilitySlot.starts_at > timestamp,
            ProfessionalAvailabilitySlot.starts_at <= (
                timestamp + timedelta(days=BOOKING_HORIZON_DAYS)
            ),
        )
        .order_by(ProfessionalAvailabilitySlot.starts_at, ProfessionalAvailabilitySlot.id)
        .limit(250)
    ).all()
    return tuple(
        BookableSlot(
            id=item.id,
            professional_id=item.professional_id,
            starts_at=ensure_utc(item.starts_at),
        ) for item in rows
    )


def validate_patient_booking_selection(
    db: Session, *, specialty_id: int, professional_id: int, slot_id: int,
) -> None:
    """Server must not trust doctor/specialty IDs chosen by browser controls."""
    if min(specialty_id, professional_id, slot_id) <= 0:
        raise SchedulingValidationError(
            "Escolha uma especialidade, um médico e um horário válido."
        )
    existing = db.exec(
        select(ProfessionalAvailabilitySlot.id)
        .join(
            Professional,
            Professional.id == ProfessionalAvailabilitySlot.professional_id,
        )
        .join(
            ProfessionalSpecialty,
            ProfessionalSpecialty.professional_id == Professional.id,
        )
        .join(Specialty, Specialty.id == ProfessionalSpecialty.specialty_id)
        .where(
            ProfessionalAvailabilitySlot.id == slot_id,
            Professional.id == professional_id,
            Professional.is_active.is_(True),
            Specialty.id == specialty_id,
            Specialty.is_active.is_(True),
        )
    ).first()
    if existing is None:
        raise SchedulingValidationError(
            "A seleção de médico, especialidade ou horário não é mais válida."
        )
