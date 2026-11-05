"""Authorized application operations for the patient reception queue."""

from sqlmodel import Session, select
from sqlalchemy import func, or_

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.profile import get_patient_operational_summary
from vitta_one.patient_queue.service import (
    PatientSearchResult,
    QueueItem,
    claim_next_patient,
    count_waiting_queue,
    create_patient,
    create_queue_entry,
    find_patient_by_cpf,
    finish_queue_entry,
    get_patient_identity,
    get_doctor_active_entry,
    list_waiting_queue,
    reassess_queue_entry,
    search_patient_identities,
    withdraw_queue_entry,
    update_patient,
)




def reception_search_patients(
    db: Session, *, token: str, query: str, limit: int = 8
) -> list[PatientSearchResult]:
    require_role(db, token, Role.RECEPCIONISTA)
    return search_patient_identities(db, query=query, limit=limit)


def reception_get_patient_identity(
    db: Session, *, token: str, patient_id: int
) -> PatientSearchResult | None:
    require_role(db, token, Role.RECEPCIONISTA)
    return get_patient_identity(db, patient_id=patient_id)


def reception_get_patient_operational_summary(
    db: Session, *, token: str, patient_id: int, history_page: int = 1,
):
    """Keep patient identity, appointments and queue metadata behind Reception RBAC."""
    require_role(db, token, Role.RECEPCIONISTA)
    return get_patient_operational_summary(
        db, patient_id=patient_id, history_page=history_page,
    )


def reception_find_patient(db: Session, *, token: str, cpf: str) -> Patient | None:
    require_role(db, token, Role.RECEPCIONISTA)
    return find_patient_by_cpf(db, cpf)


def reception_create_patient(
    db: Session,
    *,
    token: str,
    name: str,
    cpf: str,
    phone: str | None = None,
) -> Patient:
    require_role(db, token, Role.RECEPCIONISTA)
    return create_patient(db, name=name, cpf=cpf, phone=phone)


def reception_update_patient(
    db: Session,
    *,
    token: str,
    patient_id: int,
    name: str,
    phone: str | None = None,
) -> Patient:
    require_role(db, token, Role.RECEPCIONISTA)
    return update_patient(db, patient_id=patient_id, name=name, phone=phone)


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
    identity = require_role(db, token, Role.MEDICO)
    return count_waiting_queue(db, doctor_user_id=identity.id)


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



def reception_list_patient_directory(
    db: Session, *, token: str, search: str = "", page: int = 1, size: int = 10,
) -> tuple[list[dict[str, str | int]], int]:
    """Paginate patient identities after server-side receptionist authorization."""
    require_role(db, token, Role.RECEPCIONISTA)
    page = max(1, int(page))
    size = max(1, min(int(size), 30))
    term = " ".join(str(search or "").split())[:100]
    statement = select(Patient)
    if term:
        # Keep the directory search equivalent to the existing receptionist
        # quick search. Escape SQL LIKE wildcards; do not expose CPF in results.
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        digits = "".join(char for char in term if char.isdigit())
        conditions = [Patient.name.ilike(f"%{escaped}%", escape="\\")]
        if digits:
            conditions.extend((
                Patient.cpf.like(f"%{digits}%"),
                func.coalesce(Patient.phone, "").like(f"%{digits}%"),
            ))
        statement = statement.where(or_(*conditions))
    total = int(db.exec(select(func.count()).select_from(statement.subquery())).one())
    patients = db.exec(
        statement.order_by(Patient.name, Patient.id).offset((page - 1) * size).limit(size)
    ).all()
    return [
        {
            "id": patient.id, "name": patient.name,
            "phone": patient.phone or "",
            "href": f"/recepcao/pacientes/{patient.id}",
        }
        for patient in patients
    ], total
