"""Business services for availability slots and scheduled consultations."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional


class SchedulingValidationError(ValueError):
    """Raised when scheduling input violates a server-side business rule."""


class SchedulingConflictError(RuntimeError):
    """Raised when a slot or active reservation conflicts with another record."""


class SchedulingNotFoundError(LookupError):
    """Raised when a requested scheduling entity is unavailable."""


class SchedulingTransitionError(RuntimeError):
    """Raised when an entity cannot perform the requested scheduling transition."""


@dataclass(frozen=True, slots=True)
class ProfessionalOption:
    id: int
    name: str
    registration_identifier: str


@dataclass(frozen=True, slots=True)
class AvailabilitySlotItem:
    id: int
    professional_id: int
    professional_name: str
    starts_at: datetime
    status: AvailabilitySlotStatus


@dataclass(frozen=True, slots=True)
class ConsultationItem:
    id: int
    patient_id: int
    patient_name: str
    professional_id: int
    professional_name: str
    availability_slot_id: int
    scheduled_at: datetime
    status: ConsultationStatus
    cancelled_at: datetime | None


@dataclass(frozen=True, slots=True)
class AgendaSnapshot:
    slots: tuple[AvailabilitySlotItem, ...]
    consultations: tuple[ConsultationItem, ...]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime | None = None) -> datetime:
    return ensure_utc(value or utc_now())


def list_active_professionals(db: Session) -> list[ProfessionalOption]:
    rows = db.exec(
        select(Professional)
        .where(Professional.is_active.is_(True))
        .order_by(Professional.name, Professional.id)
    ).all()
    return [
        ProfessionalOption(
            id=row.id,
            name=row.name,
            registration_identifier=row.registration_identifier,
        )
        for row in rows
        if row.id is not None
    ]


def create_availability_slot(
    db: Session,
    *,
    professional_id: int,
    starts_at: datetime,
    now: datetime | None = None,
) -> ProfessionalAvailabilitySlot:
    professional = db.get(Professional, professional_id)
    if professional is None or not professional.is_active:
        raise SchedulingValidationError("Selecione um profissional ativo.")

    instant = ensure_utc(starts_at)
    if instant <= _timestamp(now):
        raise SchedulingValidationError("O horário precisa estar no futuro.")

    existing = db.exec(
        select(ProfessionalAvailabilitySlot).where(
            ProfessionalAvailabilitySlot.professional_id == professional_id,
            ProfessionalAvailabilitySlot.starts_at == instant,
        )
    ).first()
    if existing is not None:
        raise SchedulingConflictError(
            "Este profissional já possui um slot neste horário."
        )

    slot = ProfessionalAvailabilitySlot(
        professional_id=professional_id,
        starts_at=instant,
        status=AvailabilitySlotStatus.AVAILABLE.value,
    )
    db.add(slot)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SchedulingConflictError(
            "Este profissional já possui um slot neste horário."
        ) from exc
    db.refresh(slot)
    return slot


def list_availability_slots(
    db: Session,
    *,
    professional_id: int | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[AvailabilitySlotItem]:
    statement = (
        select(ProfessionalAvailabilitySlot, Professional)
        .join(Professional, Professional.id == ProfessionalAvailabilitySlot.professional_id)
    )
    if professional_id is not None:
        statement = statement.where(
            ProfessionalAvailabilitySlot.professional_id == professional_id
        )
    if start_at is not None:
        statement = statement.where(
            ProfessionalAvailabilitySlot.starts_at >= ensure_utc(start_at)
        )
    if end_at is not None:
        statement = statement.where(
            ProfessionalAvailabilitySlot.starts_at < ensure_utc(end_at)
        )
    rows = db.exec(
        statement.order_by(
            ProfessionalAvailabilitySlot.starts_at,
            Professional.name,
            ProfessionalAvailabilitySlot.id,
        )
    ).all()
    return [
        AvailabilitySlotItem(
            id=slot.id,
            professional_id=professional.id,
            professional_name=professional.name,
            starts_at=ensure_utc(slot.starts_at),
            status=AvailabilitySlotStatus(slot.status),
        )
        for slot, professional in rows
        if slot.id is not None and professional.id is not None
    ]


def set_availability_slot_active(
    db: Session,
    *,
    slot_id: int,
    is_active: bool,
    now: datetime | None = None,
) -> ProfessionalAvailabilitySlot:
    slot = db.exec(
        select(ProfessionalAvailabilitySlot)
        .where(ProfessionalAvailabilitySlot.id == slot_id)
        .with_for_update()
    ).first()
    if slot is None:
        raise SchedulingNotFoundError("O horário não está disponível.")

    current = AvailabilitySlotStatus(slot.status)
    timestamp = _timestamp(now)
    professional = db.get(Professional, slot.professional_id)

    if is_active:
        if current is not AvailabilitySlotStatus.INACTIVE:
            raise SchedulingTransitionError("Somente horários inativos podem ser reativados.")
        if ensure_utc(slot.starts_at) <= timestamp:
            raise SchedulingTransitionError("Horários passados não podem ser reativados.")
        if professional is None or not professional.is_active:
            raise SchedulingTransitionError(
                "O profissional precisa estar ativo para reativar este horário."
            )
        slot.status = AvailabilitySlotStatus.AVAILABLE.value
    else:
        if current is AvailabilitySlotStatus.BOOKED:
            raise SchedulingTransitionError(
                "Um horário reservado não pode ser desativado diretamente."
            )
        if current is not AvailabilitySlotStatus.AVAILABLE:
            raise SchedulingTransitionError("Somente horários disponíveis podem ser desativados.")
        slot.status = AvailabilitySlotStatus.INACTIVE.value

    slot.updated_at = timestamp
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def list_consultations(
    db: Session,
    *,
    professional_id: int | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[ConsultationItem]:
    statement = (
        select(Consultation, Patient, Professional)
        .join(Patient, Patient.id == Consultation.patient_id)
        .join(Professional, Professional.id == Consultation.professional_id)
    )
    if professional_id is not None:
        statement = statement.where(Consultation.professional_id == professional_id)
    if start_at is not None:
        statement = statement.where(Consultation.scheduled_at >= ensure_utc(start_at))
    if end_at is not None:
        statement = statement.where(Consultation.scheduled_at < ensure_utc(end_at))
    rows = db.exec(
        statement.order_by(Consultation.scheduled_at, Consultation.id)
    ).all()
    return [
        ConsultationItem(
            id=consultation.id,
            patient_id=patient.id,
            patient_name=patient.name,
            professional_id=professional.id,
            professional_name=professional.name,
            availability_slot_id=consultation.availability_slot_id,
            scheduled_at=ensure_utc(consultation.scheduled_at),
            status=ConsultationStatus(consultation.status),
            cancelled_at=(
                ensure_utc(consultation.cancelled_at)
                if consultation.cancelled_at is not None
                else None
            ),
        )
        for consultation, patient, professional in rows
        if consultation.id is not None and patient.id is not None and professional.id is not None
    ]


def get_agenda(
    db: Session,
    *,
    professional_id: int | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> AgendaSnapshot:
    return AgendaSnapshot(
        slots=tuple(
            list_availability_slots(
                db,
                professional_id=professional_id,
                start_at=start_at,
                end_at=end_at,
            )
        ),
        consultations=tuple(
            list_consultations(
                db,
                professional_id=professional_id,
                start_at=start_at,
                end_at=end_at,
            )
        ),
    )


def _locked_slot(db: Session, slot_id: int) -> ProfessionalAvailabilitySlot:
    slot = db.exec(
        select(ProfessionalAvailabilitySlot)
        .where(ProfessionalAvailabilitySlot.id == slot_id)
        .with_for_update()
    ).first()
    if slot is None:
        raise SchedulingNotFoundError("O horário selecionado não está disponível.")
    return slot


def _validate_bookable_slot(
    db: Session,
    slot: ProfessionalAvailabilitySlot,
    *,
    now: datetime,
) -> Professional:
    if AvailabilitySlotStatus(slot.status) is not AvailabilitySlotStatus.AVAILABLE:
        raise SchedulingConflictError("O horário selecionado não está mais disponível.")
    if ensure_utc(slot.starts_at) <= now:
        raise SchedulingValidationError("O horário selecionado já passou.")
    professional = db.get(Professional, slot.professional_id)
    if professional is None or not professional.is_active:
        raise SchedulingValidationError(
            "O profissional deste horário não está disponível para novos agendamentos."
        )
    return professional


def schedule_consultation(
    db: Session,
    *,
    patient_id: int,
    slot_id: int,
    now: datetime | None = None,
) -> Consultation:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise SchedulingValidationError("Selecione um paciente existente.")

    timestamp = _timestamp(now)
    slot = _locked_slot(db, slot_id)
    professional = _validate_bookable_slot(db, slot, now=timestamp)

    consultation = Consultation(
        patient_id=patient_id,
        professional_id=professional.id,
        availability_slot_id=slot.id,
        scheduled_at=ensure_utc(slot.starts_at),
        status=ConsultationStatus.AGENDADA.value,
        updated_at=timestamp,
    )
    slot.status = AvailabilitySlotStatus.BOOKED.value
    slot.updated_at = timestamp
    db.add(slot)
    db.add(consultation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SchedulingConflictError(
            "O horário foi reservado por outra operação. Escolha outro horário."
        ) from exc
    db.refresh(consultation)
    return consultation


def _locked_consultation(db: Session, consultation_id: int) -> Consultation:
    consultation = db.exec(
        select(Consultation)
        .where(Consultation.id == consultation_id)
        .with_for_update()
    ).first()
    if consultation is None:
        raise SchedulingNotFoundError("A consulta não está disponível.")
    return consultation


def _release_old_slot(
    db: Session,
    slot: ProfessionalAvailabilitySlot,
    *,
    now: datetime,
) -> None:
    professional = db.get(Professional, slot.professional_id)
    slot.status = (
        AvailabilitySlotStatus.AVAILABLE.value
        if ensure_utc(slot.starts_at) > now and professional is not None and professional.is_active
        else AvailabilitySlotStatus.INACTIVE.value
    )
    slot.updated_at = now
    db.add(slot)


def reschedule_consultation(
    db: Session,
    *,
    consultation_id: int,
    new_slot_id: int,
    now: datetime | None = None,
) -> Consultation:
    timestamp = _timestamp(now)
    consultation = _locked_consultation(db, consultation_id)
    if ConsultationStatus(consultation.status) is not ConsultationStatus.AGENDADA:
        raise SchedulingTransitionError(
            "Somente consultas agendadas podem ser reagendadas por este fluxo."
        )
    if consultation.availability_slot_id == new_slot_id:
        raise SchedulingValidationError("Escolha um horário diferente para reagendar.")

    ids = sorted({consultation.availability_slot_id, new_slot_id})
    locked = db.exec(
        select(ProfessionalAvailabilitySlot)
        .where(ProfessionalAvailabilitySlot.id.in_(ids))
        .order_by(ProfessionalAvailabilitySlot.id)
        .with_for_update()
    ).all()
    slots = {slot.id: slot for slot in locked if slot.id is not None}
    if len(slots) != len(ids):
        raise SchedulingNotFoundError("Um dos horários do reagendamento não está disponível.")

    old_slot = slots[consultation.availability_slot_id]
    new_slot = slots[new_slot_id]
    professional = _validate_bookable_slot(db, new_slot, now=timestamp)

    _release_old_slot(db, old_slot, now=timestamp)
    new_slot.status = AvailabilitySlotStatus.BOOKED.value
    new_slot.updated_at = timestamp
    consultation.professional_id = professional.id
    consultation.availability_slot_id = new_slot.id
    consultation.scheduled_at = ensure_utc(new_slot.starts_at)
    consultation.updated_at = timestamp
    db.add(new_slot)
    db.add(consultation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SchedulingConflictError(
            "O novo horário foi reservado por outra operação. A consulta anterior foi preservada."
        ) from exc
    db.refresh(consultation)
    return consultation


def cancel_consultation(
    db: Session,
    *,
    consultation_id: int,
    now: datetime | None = None,
) -> Consultation:
    timestamp = _timestamp(now)
    consultation = _locked_consultation(db, consultation_id)
    status = ConsultationStatus(consultation.status)
    if status is ConsultationStatus.CANCELADA:
        raise SchedulingTransitionError("Esta consulta já foi cancelada.")
    if status is not ConsultationStatus.AGENDADA:
        raise SchedulingTransitionError(
            "Somente consultas agendadas podem ser canceladas por este fluxo."
        )

    slot = _locked_slot(db, consultation.availability_slot_id)
    consultation.status = ConsultationStatus.CANCELADA.value
    consultation.cancelled_at = timestamp
    consultation.updated_at = timestamp
    _release_old_slot(db, slot, now=timestamp)
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation
