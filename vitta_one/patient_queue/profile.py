"""Privacy-limited operational projection for the Reception patient record.

Only identity, appointment status and queue metadata are returned. Clinical care
records, symptoms, prescriptions and portal credentials never enter this view.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, or_
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus


_ACTIVE_CONSULTATIONS = (
    ConsultationStatus.AGENDADA.value,
    ConsultationStatus.CONFIRMADA.value,
)
_FINAL_CONSULTATIONS = (
    ConsultationStatus.CANCELADA.value,
    ConsultationStatus.CONCLUIDA.value,
    ConsultationStatus.EM_ANDAMENTO.value,
)
_ACTIVE_QUEUE = (QueueStatus.AGUARDANDO.value, QueueStatus.EM_ATENDIMENTO.value)
_CLOSED_QUEUE = (QueueStatus.FINALIZADO.value, QueueStatus.RETIRADO.value)
_QUEUE_LABELS = {
    QueueStatus.AGUARDANDO.value: "Aguardando",
    QueueStatus.EM_ATENDIMENTO.value: "Em atendimento",
    QueueStatus.FINALIZADO.value: "Finalizado",
    QueueStatus.RETIRADO.value: "Retirado",
}


def mask_patient_cpf(cpf: str | None) -> str:
    """Never return full CPF to the detail page, including malformed values."""
    digits = "".join(character for character in str(cpf or "") if character.isdigit())
    if len(digits) != 11:
        return "Não informado"
    return f"***.***.{digits[6:9]}-{digits[9:]}"


def _consultation_row(consultation: Consultation, professional_name: str) -> dict[str, Any]:
    status = ConsultationStatus(consultation.status)
    return {
        "id": consultation.id,
        "scheduled_at": format_clinic_datetime(consultation.scheduled_at),
        "professional_name": professional_name,
        "status": status.value,
        "status_label": status.label,
    }


def _queue_row(entry: QueueEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "priority_label": QueuePriority(entry.priority).label,
        "status_label": _QUEUE_LABELS[entry.status],
        "entered_at": format_clinic_datetime(entry.entered_at),
    }


def get_patient_operational_summary(
    db: Session,
    *,
    patient_id: int,
    history_page: int = 1,
    history_size: int = 6,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Return bounded, patient-scoped administrative data without clinical fields.

    Authorization is enforced by the application-layer caller, not by the route ID.
    """
    if isinstance(patient_id, bool) or not isinstance(patient_id, int) or patient_id <= 0:
        return None
    patient = db.get(Patient, patient_id)
    if patient is None or patient.id is None:
        return None

    current = now or datetime.now(timezone.utc)
    history_size = max(1, min(int(history_size), 20))
    history_page = max(1, int(history_page))
    future_clause = and_(
        Consultation.scheduled_at >= current,
        Consultation.status.in_(_ACTIVE_CONSULTATIONS),
    )
    previous_clause = or_(
        Consultation.scheduled_at < current,
        Consultation.status.in_(_FINAL_CONSULTATIONS),
    )

    def consultation_query(clause):
        return (
            select(Consultation, Professional.name)
            .join(Professional, Professional.id == Consultation.professional_id)
            .where(Consultation.patient_id == patient.id, clause)
        )

    upcoming = db.exec(
        consultation_query(future_clause)
        .order_by(Consultation.scheduled_at, Consultation.id)
        .limit(8)
    ).all()
    history_total = int(db.exec(
        select(func.count(Consultation.id)).where(
            Consultation.patient_id == patient.id, previous_clause
        )
    ).one())
    history_pages = max(1, (history_total + history_size - 1) // history_size)
    history_page = min(history_page, history_pages)
    history = db.exec(
        consultation_query(previous_clause)
        .order_by(Consultation.scheduled_at.desc(), Consultation.id.desc())
        .offset((history_page - 1) * history_size)
        .limit(history_size)
    ).all()

    active_entry = db.exec(
        select(QueueEntry).where(
            QueueEntry.patient_id == patient.id,
            QueueEntry.status.in_(_ACTIVE_QUEUE),
        ).order_by(QueueEntry.entered_at.desc(), QueueEntry.id.desc())
    ).first()
    closed_entries = db.exec(
        select(QueueEntry).where(
            QueueEntry.patient_id == patient.id,
            QueueEntry.status.in_(_CLOSED_QUEUE),
        ).order_by(QueueEntry.entered_at.desc(), QueueEntry.id.desc()).limit(6)
    ).all()
    return {
        "id": patient.id,
        "name": patient.name,
        "cpf_masked": mask_patient_cpf(patient.cpf),
        "phone": patient.phone or "",
        "upcoming": [_consultation_row(item, doctor) for item, doctor in upcoming],
        "history": [_consultation_row(item, doctor) for item, doctor in history],
        "history_page": history_page,
        "history_pages": history_pages,
        "history_total": history_total,
        "active_queue": _queue_row(active_entry) if active_entry else None,
        "queue_history": [_queue_row(entry) for entry in closed_entries],
    }
