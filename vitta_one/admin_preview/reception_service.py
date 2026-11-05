"""Minimal, read-only reception projection for the Administrator's local QA preview.

This module does not grant reception permissions. Every entry point verifies the
local QA flag, the live Administrator session, and the role before reading data.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import and_, func, or_
from sqlmodel import Session, select

from vitta_one.admin_preview.service import require_local_admin_preview
from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import (
    clinic_date_range_to_utc,
    ensure_utc,
    format_clinic_datetime,
)
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus
from vitta_one.patient_queue.service import list_waiting_queue

MAX_PERIOD_DAYS = 31
ROW_LIMIT = 50

_PRIORITY_LABELS = {value.value: value.label for value in QueuePriority}
_STATUS_LABELS = {
    QueueStatus.AGUARDANDO.value: "Aguardando",
    QueueStatus.EM_ATENDIMENTO.value: "Em atendimento",
    QueueStatus.FINALIZADO.value: "Finalizado",
    QueueStatus.RETIRADO.value: "Retirado",
}


@dataclass(frozen=True)
class ReceptionPreviewSnapshot:
    """Only operational fields required by the protected QA screen."""

    waiting_count: int
    attending_count: int
    finalized_count: int
    withdrawn_count: int
    active_rows: list[dict[str, str]]
    history_rows: list[dict[str, str]]
    history_total: int
    consultation_rows: list[dict[str, str]]
    consultation_total: int
    professional_options: list[dict[str, str]]
    updated_at: str


def _validate_period(start_day: str, end_day: str) -> tuple[datetime, datetime]:
    """Reject invalid or unbounded periods before running any data query."""
    try:
        start_date = date.fromisoformat(start_day)
        end_date = date.fromisoformat(end_day)
    except (TypeError, ValueError) as exc:
        raise ValueError("Informe datas válidas para consultar o período.") from exc
    if end_date < start_date:
        raise ValueError("A data final deve ser igual ou posterior à inicial.")
    if (end_date - start_date).days >= MAX_PERIOD_DAYS:
        raise ValueError("Selecione um período de até 31 dias.")
    start, end = clinic_date_range_to_utc(start_day, end_day)
    assert start is not None and end is not None
    return start, end


def _priority_filter(value: str) -> str | None:
    if value == "__all__":
        return None
    if value not in _PRIORITY_LABELS:
        raise ValueError("Prioridade inválida.")
    return value


def _status_filter(value: str) -> str | None:
    if value == "__all__":
        return None
    if value not in _STATUS_LABELS:
        raise ValueError("Situação inválida.")
    return value


def _professional_filter(value: str, professionals: list[Professional]) -> int | None:
    if value == "__all__":
        return None
    try:
        requested = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Profissional inválido.") from exc
    if requested < 1 or not any(row.id == requested for row in professionals):
        raise ValueError("Profissional inválido.")
    return requested


def _active_row(
    *,
    name: str,
    priority: str,
    status: str,
    entered_at: datetime,
    professional_name: str | None,
    now: datetime,
) -> dict[str, str]:
    wait_minutes = max(0, int((now - ensure_utc(entered_at)).total_seconds() // 60))
    return {
        "patient_name": name,
        "priority": priority,
        "priority_label": _PRIORITY_LABELS[priority],
        "status": status,
        "status_label": _STATUS_LABELS[status],
        "event_at": format_clinic_datetime(entered_at),
        "professional_name": professional_name or "Não atribuído",
        "wait_label": f"{wait_minutes} min" if status == QueueStatus.AGUARDANDO.value else "—",
    }


def load_reception_preview(
    db: Session,
    *,
    token: str,
    start_day: str,
    end_day: str,
    priority_filter: str = "__all__",
    status_filter: str = "__all__",
    professional_filter: str = "__all__",
    now: datetime | None = None,
) -> ReceptionPreviewSnapshot:
    """Server-authorized snapshot, not a mutation surface or a clinical chart.

    Stock counts are live and independent of date. Finalized/withdrawn counts
    use actual transition timestamps within the selected clinic-local period.
    Status filtering affects the row lists; KPI counts remain status-wide.
    The priority filter affects both the KPIs and queue/history rows.
    """
    require_local_admin_preview(db, token)
    start, end = _validate_period(start_day, end_day)
    priority = _priority_filter(priority_filter)
    status = _status_filter(status_filter)
    current = ensure_utc(now or datetime.now(timezone.utc))

    professionals = list(db.exec(select(Professional).order_by(Professional.name)).all())
    professional_id = _professional_filter(professional_filter, professionals)
    doctor_by_user = {
        item.user_id: item.name
        for item in professionals
        if item.user_id is not None
    }

    # Reuse the same priority ordering as the actual reception queue.
    waiting_items = list_waiting_queue(db)
    if priority is not None:
        waiting_items = [item for item in waiting_items if item.priority.value == priority]

    attending_query = (
        select(QueueEntry, Patient)
        .join(Patient, Patient.id == QueueEntry.patient_id)
        .where(QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value)
        .order_by(QueueEntry.called_at, QueueEntry.id)
    )
    if priority is not None:
        attending_query = attending_query.where(QueueEntry.priority == priority)
    attending_items = list(db.exec(attending_query).all())

    active_rows: list[dict[str, str]] = []
    if status in (None, QueueStatus.AGUARDANDO.value):
        active_rows.extend(
            _active_row(
                name=item.patient_name,
                priority=item.priority.value,
                status=item.status.value,
                entered_at=item.entered_at,
                professional_name=item.professional_name,
                now=current,
            )
            for item in waiting_items[:ROW_LIMIT]
        )
    if status in (None, QueueStatus.EM_ATENDIMENTO.value):
        remaining = max(0, ROW_LIMIT - len(active_rows))
        active_rows.extend(
            _active_row(
                name=patient.name,
                priority=entry.priority,
                status=entry.status,
                entered_at=entry.entered_at,
                professional_name=doctor_by_user.get(entry.doctor_user_id),
                now=current,
            )
            for entry, patient in attending_items[:remaining]
        )

    finished_in_range = and_(
        QueueEntry.status == QueueStatus.FINALIZADO.value,
        QueueEntry.finished_at >= start,
        QueueEntry.finished_at < end,
    )
    withdrawn_in_range = and_(
        QueueEntry.status == QueueStatus.RETIRADO.value,
        QueueEntry.withdrawn_at >= start,
        QueueEntry.withdrawn_at < end,
    )
    priority_clauses = [QueueEntry.priority == priority] if priority else []
    finalized_count = int(db.exec(
        select(func.count(QueueEntry.id)).where(finished_in_range, *priority_clauses)
    ).one())
    withdrawn_count = int(db.exec(
        select(func.count(QueueEntry.id)).where(withdrawn_in_range, *priority_clauses)
    ).one())

    history_condition = or_(finished_in_range, withdrawn_in_range)
    if status in (QueueStatus.AGUARDANDO.value, QueueStatus.EM_ATENDIMENTO.value):
        # Do not conflate a current queue status with a completed passage.
        history_condition = QueueEntry.id == -1
    elif status in (QueueStatus.FINALIZADO.value, QueueStatus.RETIRADO.value):
        history_condition = finished_in_range if status == QueueStatus.FINALIZADO.value else withdrawn_in_range

    history_total = int(db.exec(
        select(func.count(QueueEntry.id)).where(history_condition, *priority_clauses)
    ).one())
    history_items = db.exec(
        select(QueueEntry, Patient)
        .join(Patient, Patient.id == QueueEntry.patient_id)
        .where(history_condition, *priority_clauses)
        .order_by(func.coalesce(QueueEntry.finished_at, QueueEntry.withdrawn_at).desc(), QueueEntry.id.desc())
        .limit(ROW_LIMIT)
    ).all()
    history_rows = [
        {
            "patient_name": patient.name,
            "priority": entry.priority,
            "priority_label": _PRIORITY_LABELS[entry.priority],
            "status": entry.status,
            "status_label": _STATUS_LABELS[entry.status],
            "event_at": format_clinic_datetime(
                entry.finished_at if entry.status == QueueStatus.FINALIZADO.value else entry.withdrawn_at
            ),
            "professional_name": doctor_by_user.get(entry.doctor_user_id, "Não atribuído"),
            "wait_label": "",
        }
        for entry, patient in history_items
    ]

    consultation_clauses = [
        Consultation.scheduled_at >= start,
        Consultation.scheduled_at < end,
    ]
    if professional_id is not None:
        consultation_clauses.append(Consultation.professional_id == professional_id)
    consultation_total = int(db.exec(
        select(func.count(Consultation.id)).where(*consultation_clauses)
    ).one())
    # Read only schedule metadata; no patient identifiers or clinical content.
    consultation_items = db.exec(
        select(Consultation, Professional)
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(*consultation_clauses)
        .order_by(Consultation.scheduled_at, Consultation.id)
        .limit(ROW_LIMIT)
    ).all()
    consultation_rows = [
        {
            "professional_name": professional.name,
            "scheduled_at": format_clinic_datetime(consultation.scheduled_at),
            "status": consultation.status,
            "status_label": ConsultationStatus(consultation.status).label,
        }
        for consultation, professional in consultation_items
    ]

    return ReceptionPreviewSnapshot(
        waiting_count=len(waiting_items),
        attending_count=len(attending_items),
        finalized_count=finalized_count,
        withdrawn_count=withdrawn_count,
        active_rows=active_rows,
        history_rows=history_rows,
        history_total=history_total,
        consultation_rows=consultation_rows,
        consultation_total=consultation_total,
        professional_options=[
            {"label": item.name, "value": str(item.id)}
            for item in professionals if item.id is not None
        ],
        updated_at=format_clinic_datetime(current),
    )
