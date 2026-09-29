"""Authorized application operations for the patient reception queue."""

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.service import (
    QueueItem,
    claim_next_patient,
    count_waiting_queue,
    create_patient,
    create_queue_entry,
    find_patient_by_cpf,
    finish_queue_entry,
    get_doctor_active_entry,
    list_waiting_queue,
    reassess_queue_entry,
    withdraw_queue_entry,
)


def reception_find_patient(db: Session, *, token: str, cpf: str) -> Patient | None:
    require_role(db, token, Role.RECEPCIONISTA)
    return find_patient_by_cpf(db, cpf)


def reception_create_patient(
    db: Session, *, token: str, name: str, cpf: str
) -> Patient:
    require_role(db, token, Role.RECEPCIONISTA)
    return create_patient(db, name=name, cpf=cpf)


def reception_list_queue(db: Session, *, token: str) -> list[QueueItem]:
    require_role(db, token, Role.RECEPCIONISTA)
    return list_waiting_queue(db)


def reception_enqueue(
    db: Session,
    *,
    token: str,
    patient_id: int,
    symptoms: str,
    priority: str,
) -> QueueEntry:
    require_role(db, token, Role.RECEPCIONISTA)
    return create_queue_entry(
        db,
        patient_id=patient_id,
        symptoms=symptoms,
        priority=priority,
    )


def reception_reassess(
    db: Session,
    *,
    token: str,
    entry_id: int,
    symptoms: str,
    priority: str,
) -> QueueEntry:
    require_role(db, token, Role.RECEPCIONISTA)
    return reassess_queue_entry(
        db,
        entry_id=entry_id,
        symptoms=symptoms,
        priority=priority,
    )


def reception_withdraw(
    db: Session, *, token: str, entry_id: int, reason: str
) -> QueueEntry:
    require_role(db, token, Role.RECEPCIONISTA)
    return withdraw_queue_entry(db, entry_id=entry_id, reason=reason)


def doctor_waiting_count(db: Session, *, token: str) -> int:
    require_role(db, token, Role.MEDICO)
    return count_waiting_queue(db)


def doctor_active_queue_entry(db: Session, *, token: str) -> QueueItem | None:
    identity = require_role(db, token, Role.MEDICO)
    return get_doctor_active_entry(db, doctor_user_id=identity.id)


def doctor_claim_next(db: Session, *, token: str) -> QueueItem:
    identity = require_role(db, token, Role.MEDICO)
    return claim_next_patient(db, doctor_user_id=identity.id)


def doctor_finish(db: Session, *, token: str, entry_id: int) -> QueueEntry:
    identity = require_role(db, token, Role.MEDICO)
    return finish_queue_entry(
        db,
        entry_id=entry_id,
        doctor_user_id=identity.id,
    )
