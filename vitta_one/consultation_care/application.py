"""Authorized application operations for consultation arrival and care lifecycle."""

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.patient_queue import QueueEntry


def reception_confirm_arrival(
    db: Session,
    *,
    token: str,
    consultation_id: int,
    symptoms: str,
    priority: str,
) -> QueueEntry:
    require_role(db, token, Role.RECEPCIONISTA)
    return confirm_arrival(
        db,
        consultation_id=consultation_id,
        symptoms=symptoms,
        priority=priority,
    )
