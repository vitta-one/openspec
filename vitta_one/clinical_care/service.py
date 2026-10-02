"""Clinical care record business services and protected history projections."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.models.appointment import Consultation
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.models.professional import Professional
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
    consultation_id: int
    patient_id: int
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
    consultation_id: int
    patient_id: int
    professional_name: str
    scheduled_at: datetime
    completed_at: datetime
    chief_complaint: str
    anamnesis: str
    diagnosis: str
    conduct_notes: str


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


def _active_context(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    lock: bool,
) -> tuple[QueueEntry, Consultation, ClinicalCareRecord, Professional]:
    entry_statement = select(QueueEntry).where(
        QueueEntry.id == entry_id,
        QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value,
        QueueEntry.doctor_user_id == doctor_user_id,
    )
    if lock:
        entry_statement = entry_statement.with_for_update()
    entry = db.exec(entry_statement).first()
    if entry is None:
        raise ClinicalCareNotFoundError("Não há atendimento clínico ativo autorizado.")
    if entry.consultation_id is None:
        raise ClinicalCareNotFoundError(
            "Atendimentos avulsos ainda não possuem registro clínico nesta etapa."
        )

    consultation_statement = select(Consultation).where(
        Consultation.id == entry.consultation_id
    )
    if lock:
        consultation_statement = consultation_statement.with_for_update()
    consultation = db.exec(consultation_statement).first()
    if consultation is None or consultation.patient_id != entry.patient_id:
        raise ClinicalCareNotFoundError("O contexto clínico ativo está inconsistente.")
    if ConsultationStatus(consultation.status) is not ConsultationStatus.EM_ANDAMENTO:
        raise ClinicalCareTransitionError(
            "O registro clínico só pode ser alterado durante a consulta em andamento."
        )

    professional = db.get(Professional, consultation.professional_id)
    if professional is None or professional.user_id != doctor_user_id:
        raise ClinicalCareAuthorizationError(
            "O atendimento clínico pertence a outro profissional."
        )

    record_statement = select(ClinicalCareRecord).where(
        ClinicalCareRecord.consultation_id == consultation.id
    )
    if lock:
        record_statement = record_statement.with_for_update()
    record = db.exec(record_statement).first()
    if record is None:
        raise ClinicalCareNotFoundError(
            "O registro clínico desta consulta não está disponível."
        )
    if (
        record.patient_id != consultation.patient_id
        or record.doctor_user_id != doctor_user_id
    ):
        raise ClinicalCareAuthorizationError(
            "O registro clínico não pertence ao atendimento autenticado."
        )

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
    """Read-only completed-care projection used by authorized callers."""
    if page_size <= 0:
        raise ClinicalCareValidationError("O tamanho da página deve ser positivo.")

    base_filters = (
        ClinicalCareRecord.patient_id == patient_id,
        Consultation.status == ConsultationStatus.CONCLUIDA.value,
        Consultation.completed_at.is_not(None),
    )
    total = int(
        db.exec(
            select(func.count(ClinicalCareRecord.id))
            .join(
                Consultation,
                Consultation.id == ClinicalCareRecord.consultation_id,
            )
            .where(*base_filters)
        ).one()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)
    safe_page = min(max(int(page or 1), 1), total_pages)
    offset = (safe_page - 1) * page_size

    rows = db.exec(
        select(ClinicalCareRecord, Consultation, Professional)
        .join(
            Consultation,
            Consultation.id == ClinicalCareRecord.consultation_id,
        )
        .join(Professional, Professional.id == Consultation.professional_id)
        .where(*base_filters)
        .order_by(Consultation.completed_at.desc(), Consultation.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    items: list[ClinicalHistoryItem] = []
    for record, consultation, professional in rows:
        if record.id is None or consultation.id is None or consultation.completed_at is None:
            continue
        items.append(
            ClinicalHistoryItem(
                record_id=record.id,
                consultation_id=consultation.id,
                patient_id=record.patient_id,
                professional_name=professional.name,
                scheduled_at=_as_utc(consultation.scheduled_at),
                completed_at=_as_utc(consultation.completed_at),
                chief_complaint=record.chief_complaint,
                anamnesis=record.anamnesis,
                diagnosis=record.diagnosis,
                conduct_notes=record.conduct_notes,
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
    _, consultation, _, _ = _active_context(
        db,
        entry_id=entry_id,
        doctor_user_id=doctor_user_id,
        lock=False,
    )
    return list_completed_history_for_patient(
        db,
        patient_id=consultation.patient_id,
        page=page,
        page_size=CLINICAL_HISTORY_PAGE_SIZE,
    )
