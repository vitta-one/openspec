"""Shared transactional guard for scheduled and walk-in arrivals."""

from sqlmodel import Session, select

from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.domain import QueueStatus


class ActiveQueueEntryError(RuntimeError):
    """Another active queue passage already belongs to this patient."""


def lock_patient_queue_slot(db: Session, *, patient_id: int) -> Patient | None:
    """Serialize active arrival creation per patient on PostgreSQL."""
    patient = db.exec(
        select(Patient).where(Patient.id == patient_id).with_for_update()
    ).first()
    if patient is None:
        return None
    active = db.exec(
        select(QueueEntry.id)
        .where(
            QueueEntry.patient_id == patient_id,
            QueueEntry.status.in_(
                (QueueStatus.AGUARDANDO.value, QueueStatus.EM_ATENDIMENTO.value)
            ),
        )
        .limit(1)
    ).first()
    if active is not None:
        raise ActiveQueueEntryError(
            "Este paciente já possui uma entrada ativa na fila."
        )
    return patient
