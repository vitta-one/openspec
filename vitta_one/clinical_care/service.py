"""Clinical care record business services and protected history projections."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.models.appointment import Consultation
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.models.auth import User
from vitta_one.clinical_prescription.service import (
    PrescriptionView,
    list_prescriptions_for_records,
)
from vitta_one.patient_queue.domain import QueueStatus

CLINICAL_HISTORY_PAGE_SIZE = 10

_FIELD_LIMITS = {
    "chief_complaint": ("Queixa principal", 4_000),
    "anamnesis": ("Anamnese", 12_000),
    "diagnosis": ("Diagnóstico", 6_000),
    "conduct_notes": ("Conduta e observações", 8_000),
}


class ClinicalCareValidationError(ValueError):
    """Raised when clinical text or paging input is invalid."""


class ClinicalCareNotFoundError(LookupError):
    """Raised when the active authorized clinical context does not exist."""


class ClinicalCareAuthorizationError(PermissionError):
    """Raised when a doctor is not allowed to access a clinical record."""


class ClinicalCareTransitionError(RuntimeError):
    """Raised when the linked Consultation is not editable."""


class ClinicalCareConflictError(RuntimeError):
    """Raised when a one-record-per-Consultation invariant is violated."""


@dataclass(frozen=True, slots=True)
class ClinicalCareRecordItem:
    id: int
    consultation_id: int | None
    patient_id: int
    queue_entry_id: int | None
    doctor_user_id: int
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ClinicalHistoryItem:
    record_id: int
    consultation_id: int | None
    patient_id: int
    professional_name: str
    scheduled_at: datetime
    completed_at: datetime
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str
    prescriptions: tuple[PrescriptionView, ...]


@dataclass(frozen=True, slots=True)
class ClinicalHistoryPage:
    items: tuple[ClinicalHistoryItem, ...]
    page: int
    page_size: int
    total_count: int
    total_pages: int


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    return ensure_utc(value)


def _normalize_field(field: str, value: str) -> str:
    clean = str(value or "").strip()
    label, limit = _FIELD_LIMITS[field]
    if len(clean) > limit:
        raise ClinicalCareValidationError(
            f"{label} excede o limite de {limit} caracteres."
        )
    return clean


def _to_item(record: ClinicalCareRecord) -> ClinicalCareRecordItem:
    if record.id is None:
        raise RuntimeError("Registro clínico persistido sem identificador.")
    return ClinicalCareRecordItem(
        id=record.id,
        consultation_id=record.consultation_id,
        queue_entry_id=record.queue_entry_id,
        patient_id=record.patient_id,
        doctor_user_id=record.doctor_user_id,
        chief_complaint=record.chief_complaint,
        anamnesis=record.anamnesis,
        diagnosis=record.diagnosis,
        conduct_notes=record.conduct_notes,
        created_at=_as_utc(record.created_at),
        updated_at=_as_utc(record.updated_at),
    )


def create_record_for_consultation_start(
    db: Session,
    *,
    consultation: Consultation,
    doctor_user_id: int,
    now: datetime,
) -> ClinicalCareRecord:
    """Create the empty record in the caller's transaction before care begins."""
    if consultation.id is None:
        raise ClinicalCareValidationError("A consulta ainda não está persistida.")

    existing = db.exec(
        select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    ).first()
    if existing is not None:
        raise ClinicalCareConflictError(
            "Esta consulta já possui um registro clínico."
        )

    timestamp = _as_utc(now)
    record = ClinicalCareRecord(
        consultation_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_user_id=doctor_user_id,
        chief_complaint="",
        anamnesis="",
        diagnosis="",
        conduct_notes="",
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(record)
    return record


def create_record_for_queue_start(
    db: Session, *, entry: QueueEntry, doctor_user_id: int, now: datetime
) -> ClinicalCareRecord:
    """Create one walk-in clinical record inside the atomic queue-claim transaction."""
    if entry.id is None or entry.consultation_id is not None:
        raise ClinicalCareValidationError("Entrada avulsa de fila inválida.")
    if db.exec(
        select(ClinicalCareRecord).where(ClinicalCareRecord.queue_entry_id == entry.id)
    ).first() is not None:
        raise ClinicalCareConflictError("Esta passagem já possui registro clínico.")
    stamp = _as_utc(now)
    record = ClinicalCareRecord(
        consultation_id=None,
        queue_entry_id=entry.id,
        patient_id=entry.patient_id,
        doctor_user_id=doctor_user_id,
        chief_complaint="",
        anamnesis="",
        diagnosis="",
        conduct_notes="",
        created_at=stamp,
        updated_at=stamp,
    )
    db.add(record)
    return record


def _active_context(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    lock: bool,
) -> tuple[QueueEntry, Consultation | None, ClinicalCareRecord, Professional | None]:
    entry_stmt = select(QueueEntry).where(
        QueueEntry.id == entry_id,
        QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value,
        QueueEntry.doctor_user_id == doctor_user_id,
    )
    if lock:
        entry_stmt = entry_stmt.with_for_update()
    entry = db.exec(entry_stmt).first()
    if entry is None:
        raise ClinicalCareNotFoundError("Não há atendimento clínico ativo autorizado.")

    consultation: Consultation | None = None
    if entry.consultation_id is not None:
        stmt = select(Consultation).where(Consultation.id == entry.consultation_id)
        if lock:
            stmt = stmt.with_for_update()
        consultation = db.exec(stmt).first()
        if consultation is None or consultation.patient_id != entry.patient_id:
            raise ClinicalCareNotFoundError("O contexto clínico ativo está inconsistente.")
        if ConsultationStatus(consultation.status) is not ConsultationStatus.EM_ANDAMENTO:
            raise ClinicalCareTransitionError(
                "O prontuário só pode ser editado com atendimento em andamento."
            )
        professional = db.get(Professional, consultation.professional_id)
        if professional is None or professional.user_id != doctor_user_id:
            raise ClinicalCareAuthorizationError(
                "O atendimento clínico pertence a outro profissional."
            )
        stmt = select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    else:
        professional = db.exec(
            select(Professional).where(Professional.user_id == doctor_user_id)
        ).first()
        stmt = select(ClinicalCareRecord).where(
            ClinicalCareRecord.queue_entry_id == entry.id
        )
    if lock:
        stmt = stmt.with_for_update()
    record = db.exec(stmt).first()
    if record is None:
        raise ClinicalCareNotFoundError(
            "O registro clínico deste atendimento não está disponível."
        )
    if record.patient_id != entry.patient_id or record.doctor_user_id != doctor_user_id:
        raise ClinicalCareAuthorizationError(
            "O registro clínico não pertence ao atendimento autenticado."
        )
    if (consultation is None and record.consultation_id is not None) or (
        consultation is not None and record.queue_entry_id is not None
    ):
        raise ClinicalCareAuthorizationError("O vínculo do atendimento está inconsistente.")
    return entry, consultation, record, professional

def get_active_record(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
) -> ClinicalCareRecordItem:
    _, _, record, _ = _active_context(
        db,
        entry_id=entry_id,
        doctor_user_id=doctor_user_id,
        lock=False,
    )
    return _to_item(record)


def save_active_record(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    chief_complaint: str,
    anamnesis: str,
    diagnosis: str,
    conduct_notes: str,
    now: datetime | None = None,
) -> ClinicalCareRecordItem:
    """Persist one clinical draft after locking and revalidating the active context."""
    _, _, record, _ = _active_context(
        db,
        entry_id=entry_id,
        doctor_user_id=doctor_user_id,
        lock=True,
    )

    values = {
        "chief_complaint": _normalize_field("chief_complaint", chief_complaint),
        "anamnesis": _normalize_field("anamnesis", anamnesis),
        "diagnosis": _normalize_field("diagnosis", diagnosis),
        "conduct_notes": _normalize_field("conduct_notes", conduct_notes),
    }
    record.chief_complaint = values["chief_complaint"]
    record.anamnesis = values["anamnesis"]
    record.diagnosis = values["diagnosis"]
    record.conduct_notes = values["conduct_notes"]
    record.updated_at = _as_utc(now or utc_now())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_item(record)


def list_completed_history_for_patient(
    db: Session,
    *,
    patient_id: int,
    page: int = 1,
    page_size: int = CLINICAL_HISTORY_PAGE_SIZE,
) -> ClinicalHistoryPage:
    """Read completed scheduled and walk-in care, newest first; never show active drafts."""
    if page_size <= 0:
        raise ClinicalCareValidationError("O tamanho da página deve ser positivo.")
    base = (
        ClinicalCareRecord.patient_id == patient_id,
        or_(
            and_(
                ClinicalCareRecord.consultation_id.is_not(None),
                Consultation.status == ConsultationStatus.CONCLUIDA.value,
                Consultation.completed_at.is_not(None),
            ),
            and_(
                ClinicalCareRecord.queue_entry_id.is_not(None),
                QueueEntry.status == QueueStatus.FINALIZADO.value,
                QueueEntry.finished_at.is_not(None),
            ),
        ),
    )
    joined = (
        select(ClinicalCareRecord, Consultation, QueueEntry)
        .outerjoin(Consultation, Consultation.id == ClinicalCareRecord.consultation_id)
        .outerjoin(QueueEntry, QueueEntry.id == ClinicalCareRecord.queue_entry_id)
        .where(*base)
    )
    count_stmt = (
        select(func.count(ClinicalCareRecord.id))
        .outerjoin(Consultation, Consultation.id == ClinicalCareRecord.consultation_id)
        .outerjoin(QueueEntry, QueueEntry.id == ClinicalCareRecord.queue_entry_id)
        .where(*base)
    )
    total = int(db.exec(count_stmt).one())
    total_pages = max(1, (total + page_size - 1) // page_size)
    safe_page = min(max(int(page or 1), 1), total_pages)
    rows = db.exec(
        joined.order_by(
            func.coalesce(QueueEntry.finished_at, Consultation.completed_at).desc(),
            ClinicalCareRecord.id.desc(),
        ).offset((safe_page - 1) * page_size).limit(page_size)
    ).all()
    record_ids = [record.id for record, _, _ in rows if record.id is not None]
    prescriptions = list_prescriptions_for_records(
        db, clinical_care_record_ids=record_ids
    )
    items: list[ClinicalHistoryItem] = []
    for record, consultation, entry in rows:
        completed = consultation.completed_at if consultation else (entry.finished_at if entry else None)
        if record.id is None or completed is None:
            continue
        if consultation is not None:
            professional = db.get(Professional, consultation.professional_id)
            started = consultation.scheduled_at
        else:
            professional = db.exec(
                select(Professional).where(Professional.user_id == record.doctor_user_id)
            ).first()
            started = entry.called_at or entry.entered_at
        items.append(
            ClinicalHistoryItem(
                record_id=record.id,
                consultation_id=record.consultation_id,
                patient_id=record.patient_id,
                professional_name=professional.name if professional else "Médico responsável",
                scheduled_at=_as_utc(started),
                completed_at=_as_utc(completed),
                chief_complaint=record.chief_complaint,
                anamnesis=record.anamnesis,
                diagnosis=record.diagnosis,
                conduct_notes=record.conduct_notes,
                prescriptions=prescriptions.get(record.id, ()),
            )
        )
    return ClinicalHistoryPage(
        items=tuple(items),
        page=safe_page,
        page_size=page_size,
        total_count=total,
        total_pages=total_pages,
    )

def list_history_for_active_entry(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    page: int = 1,
) -> ClinicalHistoryPage:
    entry, _, _, _ = _active_context(
        db, entry_id=entry_id, doctor_user_id=doctor_user_id, lock=False
    )
    return list_completed_history_for_patient(
        db,
        patient_id=entry.patient_id,
        page=page,
        page_size=CLINICAL_HISTORY_PAGE_SIZE,
    )

