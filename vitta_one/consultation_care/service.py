"""Transactional bridge between scheduled Consultations and the operational queue."""

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import release_reserved_slot
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.domain import QueueStatus
from vitta_one.patient_queue.validation import (
    QueuePayloadValidationError,
    normalize_queue_symptoms,
    parse_queue_priority,
)
from vitta_one.auth.roles import Role


class CareLifecycleValidationError(ValueError):
    """Raised when an arrival or lifecycle input is not valid."""


class CareLifecycleConflictError(RuntimeError):
    """Raised when concurrent work conflicts with a lifecycle transition."""


class CareLifecycleTransitionError(RuntimeError):
    """Raised when a Consultation cannot perform the requested transition."""


class CareLifecycleAssignmentError(PermissionError):
    """Raised when the authenticated doctor is not the scheduled professional."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _locked_consultation(db: Session, consultation_id: int) -> Consultation:
    consultation = db.exec(
        select(Consultation)
        .where(Consultation.id == consultation_id)
        .with_for_update()
    ).first()
    if consultation is None:
        raise CareLifecycleValidationError("A consulta não está disponível.")
    return consultation


def _scheduled_professional(db: Session, consultation: Consultation) -> Professional:
    professional = db.get(Professional, consultation.professional_id)
    if professional is None:
        raise CareLifecycleValidationError("O profissional da consulta não está disponível.")
    return professional


def _validate_arrival_professional(db: Session, consultation: Consultation) -> Professional:
    professional = _scheduled_professional(db, consultation)
    if not professional.is_active:
        raise CareLifecycleValidationError(
            "O profissional desta consulta está inativo. Corrija o cadastro antes de confirmar a chegada."
        )
    if professional.user_id is None:
        raise CareLifecycleValidationError(
            "Vincule uma conta Médica ao profissional antes de confirmar a chegada."
        )
    user = db.get(User, professional.user_id)
    if user is None or user.role != Role.MEDICO.value:
        raise CareLifecycleValidationError(
            "A conta vinculada ao profissional precisa existir e possuir a role Médico."
        )
    return professional


def confirm_arrival(
    db: Session,
    *,
    consultation_id: int,
    symptoms: str,
    priority: str,
    now: datetime | None = None,
) -> QueueEntry:
    """Confirm physical arrival and create exactly one waiting QueueEntry atomically."""
    timestamp = _as_utc(now or utc_now())
    consultation = _locked_consultation(db, consultation_id)
    if ConsultationStatus(consultation.status) is not ConsultationStatus.AGENDADA:
        raise CareLifecycleTransitionError(
            "Somente consultas agendadas podem ter a chegada confirmada."
        )

    patient = db.get(Patient, consultation.patient_id)
    if patient is None:
        raise CareLifecycleValidationError("O paciente desta consulta não está disponível.")
    _validate_arrival_professional(db, consultation)

    existing = db.exec(
        select(QueueEntry).where(QueueEntry.consultation_id == consultation_id)
    ).first()
    if existing is not None:
        raise CareLifecycleConflictError(
            "A chegada desta consulta já possui uma entrada de fila."
        )

    try:
        clean_symptoms = normalize_queue_symptoms(symptoms)
        parsed_priority = parse_queue_priority(priority)
    except QueuePayloadValidationError as exc:
        raise CareLifecycleValidationError(str(exc)) from exc

    entry = QueueEntry(
        patient_id=consultation.patient_id,
        consultation_id=consultation.id,
        symptoms=clean_symptoms,
        priority=parsed_priority.value,
        status=QueueStatus.AGUARDANDO.value,
        entered_at=timestamp,
        updated_at=timestamp,
    )
    consultation.status = ConsultationStatus.CONFIRMADA.value
    consultation.confirmed_at = timestamp
    consultation.updated_at = timestamp
    db.add(entry)
    db.add(consultation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CareLifecycleConflictError(
            "A chegada desta consulta já foi confirmada por outra operação."
        ) from exc
    db.refresh(entry)
    return entry


def start_linked_consultation(
    db: Session,
    *,
    consultation_id: int,
    doctor_user_id: int,
    now: datetime,
) -> Consultation:
    """Transition CONFIRMADA -> EM_ANDAMENTO without committing."""
    consultation = _locked_consultation(db, consultation_id)
    if ConsultationStatus(consultation.status) is not ConsultationStatus.CONFIRMADA:
        raise CareLifecycleTransitionError(
            "A consulta vinculada não está confirmada para iniciar o atendimento."
        )
    professional = _scheduled_professional(db, consultation)
    if professional.user_id != doctor_user_id:
        raise CareLifecycleAssignmentError(
            "Esta consulta está vinculada a outro profissional."
        )

    timestamp = _as_utc(now)
    consultation.status = ConsultationStatus.EM_ANDAMENTO.value
    consultation.started_at = timestamp
    consultation.updated_at = timestamp
    db.add(consultation)
    return consultation


def complete_linked_consultation(
    db: Session,
    *,
    consultation_id: int,
    doctor_user_id: int,
    now: datetime,
) -> Consultation:
    """Transition EM_ANDAMENTO -> CONCLUIDA without committing."""
    consultation = _locked_consultation(db, consultation_id)
    if ConsultationStatus(consultation.status) is not ConsultationStatus.EM_ANDAMENTO:
        raise CareLifecycleTransitionError(
            "A consulta vinculada não está em andamento para ser concluída."
        )
    professional = _scheduled_professional(db, consultation)
    if professional.user_id != doctor_user_id:
        raise CareLifecycleAssignmentError(
            "Esta consulta está vinculada a outro profissional."
        )

    timestamp = _as_utc(now)
    consultation.status = ConsultationStatus.CONCLUIDA.value
    consultation.completed_at = timestamp
    consultation.updated_at = timestamp
    db.add(consultation)
    return consultation


def cancel_linked_consultation_from_queue(
    db: Session,
    *,
    consultation_id: int,
    now: datetime,
) -> Consultation:
    """Transition CONFIRMADA -> CANCELADA after a waiting queue withdrawal."""
    consultation = _locked_consultation(db, consultation_id)
    if ConsultationStatus(consultation.status) is not ConsultationStatus.CONFIRMADA:
        raise CareLifecycleTransitionError(
            "A consulta vinculada não está confirmada para retirada da fila."
        )

    slot = db.exec(
        select(ProfessionalAvailabilitySlot)
        .where(ProfessionalAvailabilitySlot.id == consultation.availability_slot_id)
        .with_for_update()
    ).first()
    if slot is None:
        raise CareLifecycleValidationError("O horário vinculado à consulta não está disponível.")

    timestamp = _as_utc(now)
    consultation.status = ConsultationStatus.CANCELADA.value
    consultation.cancelled_at = timestamp
    consultation.updated_at = timestamp
    release_reserved_slot(db, slot, now=timestamp)
    db.add(consultation)
    return consultation
