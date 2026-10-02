"""Prescription domain services with lifecycle, ownership and locking rules."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.models.appointment import Consultation
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_prescription import Prescription, PrescriptionItem
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional

MEDICATION_LIMIT = 300
INSTRUCTIONS_LIMIT = 2_000
ITEM_NOTES_LIMIT = 2_000
GENERAL_NOTES_LIMIT = 4_000


class PrescriptionValidationError(ValueError):
    """Raised when prescription input violates the explicit text contract."""


class PrescriptionAuthorizationError(PermissionError):
    """Raised when a doctor does not own the prescription context."""


class PrescriptionTransitionError(RuntimeError):
    """Raised when the linked Consultation does not allow the requested mutation."""


class PrescriptionConflictError(RuntimeError):
    """Raised when concurrency or invariants prevent a safe mutation."""


class PrescriptionNotFoundError(LookupError):
    """Raised when an authorized prescription context cannot be resolved."""


@dataclass(frozen=True, slots=True)
class PrescriptionItemView:
    id: int
    prescription_id: int
    medication_or_item: str
    instructions: str
    notes: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PrescriptionView:
    id: int
    clinical_care_record_id: int
    consultation_id: int
    doctor_user_id: int
    general_notes: str
    created_at: datetime
    updated_at: datetime
    items: tuple[PrescriptionItemView, ...]


@dataclass(frozen=True, slots=True)
class PrintablePrescriptionView:
    prescription: PrescriptionView
    patient_name: str
    professional_name: str
    registration_identifier: str
    scheduled_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    return ensure_utc(value)


def _required_text(value: str, *, label: str, limit: int) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise PrescriptionValidationError(f"Informe {label}.")
    if len(clean) > limit:
        raise PrescriptionValidationError(
            f"{label.capitalize()} excede o limite de {limit} caracteres."
        )
    return clean


def _optional_text(value: str, *, label: str, limit: int) -> str:
    clean = str(value or "").strip()
    if len(clean) > limit:
        raise PrescriptionValidationError(
            f"{label.capitalize()} excede o limite de {limit} caracteres."
        )
    return clean


def _validate_item(
    *,
    medication_or_item: str,
    instructions: str,
    notes: str,
) -> tuple[str, str, str]:
    return (
        _required_text(
            medication_or_item,
            label="o medicamento ou item",
            limit=MEDICATION_LIMIT,
        ),
        _required_text(
            instructions,
            label="a orientação ou posologia",
            limit=INSTRUCTIONS_LIMIT,
        ),
        _optional_text(
            notes,
            label="observações do item",
            limit=ITEM_NOTES_LIMIT,
        ),
    )


def _validate_general_notes(value: str) -> str:
    return _optional_text(
        value,
        label="observações gerais",
        limit=GENERAL_NOTES_LIMIT,
    )


def _record_context(
    db: Session,
    *,
    clinical_care_record_id: int,
    doctor_user_id: int,
    editable: bool,
    lock: bool,
) -> tuple[ClinicalCareRecord, Consultation, Professional]:
    record_stmt = select(ClinicalCareRecord).where(
        ClinicalCareRecord.id == clinical_care_record_id
    )
    if lock:
        record_stmt = record_stmt.with_for_update()
    record = db.exec(record_stmt).first()
    if record is None:
        raise PrescriptionNotFoundError("O Atendimento clínico não está disponível.")

    consultation_stmt = select(Consultation).where(
        Consultation.id == record.consultation_id
    )
    if lock:
        consultation_stmt = consultation_stmt.with_for_update()
    consultation = db.exec(consultation_stmt).first()
    if consultation is None or consultation.patient_id != record.patient_id:
        raise PrescriptionNotFoundError("O contexto da Prescrição está inconsistente.")

    professional = db.get(Professional, consultation.professional_id)
    if (
        record.doctor_user_id != doctor_user_id
        or professional is None
        or professional.user_id != doctor_user_id
    ):
        raise PrescriptionAuthorizationError(
            "A Prescrição pertence a outro profissional."
        )

    status = ConsultationStatus(consultation.status)
    if editable and status is not ConsultationStatus.EM_ANDAMENTO:
        raise PrescriptionTransitionError(
            "Prescrições só podem ser alteradas durante a Consulta em andamento."
        )
    return record, consultation, professional


def _prescription_context(
    db: Session,
    *,
    prescription_id: int,
    doctor_user_id: int,
    editable: bool,
    lock: bool,
) -> tuple[Prescription, ClinicalCareRecord, Consultation, Professional]:
    stmt = select(Prescription).where(Prescription.id == prescription_id)
    if lock:
        stmt = stmt.with_for_update()
    prescription = db.exec(stmt).first()
    if prescription is None:
        raise PrescriptionNotFoundError("A Prescrição não está disponível.")

    record, consultation, professional = _record_context(
        db,
        clinical_care_record_id=prescription.clinical_care_record_id,
        doctor_user_id=doctor_user_id,
        editable=editable,
        lock=lock,
    )
    if (
        prescription.consultation_id != consultation.id
        or prescription.clinical_care_record_id != record.id
        or prescription.doctor_user_id != doctor_user_id
    ):
        raise PrescriptionAuthorizationError(
            "A Prescrição não pertence ao Atendimento autenticado."
        )
    return prescription, record, consultation, professional


def _item_view(item: PrescriptionItem) -> PrescriptionItemView:
    if item.id is None:
        raise RuntimeError("Item de Prescrição persistido sem identificador.")
    return PrescriptionItemView(
        id=item.id,
        prescription_id=item.prescription_id,
        medication_or_item=item.medication_or_item,
        instructions=item.instructions,
        notes=item.notes,
        created_at=_as_utc(item.created_at),
        updated_at=_as_utc(item.updated_at),
    )


def _views_for_prescriptions(
    db: Session,
    prescriptions: list[Prescription],
) -> tuple[PrescriptionView, ...]:
    if not prescriptions:
        return ()
    ids = [item.id for item in prescriptions if item.id is not None]
    item_rows = list(
        db.exec(
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id.in_(ids))
            .order_by(
                PrescriptionItem.prescription_id,
                PrescriptionItem.created_at,
                PrescriptionItem.id,
            )
        ).all()
    )
    items_by_prescription: dict[int, list[PrescriptionItemView]] = {}
    for item in item_rows:
        items_by_prescription.setdefault(item.prescription_id, []).append(
            _item_view(item)
        )

    views: list[PrescriptionView] = []
    for prescription in prescriptions:
        if prescription.id is None:
            continue
        views.append(
            PrescriptionView(
                id=prescription.id,
                clinical_care_record_id=prescription.clinical_care_record_id,
                consultation_id=prescription.consultation_id,
                doctor_user_id=prescription.doctor_user_id,
                general_notes=prescription.general_notes,
                created_at=_as_utc(prescription.created_at),
                updated_at=_as_utc(prescription.updated_at),
                items=tuple(items_by_prescription.get(prescription.id, [])),
            )
        )
    return tuple(views)


def list_prescriptions_for_records(
    db: Session,
    *,
    clinical_care_record_ids: list[int] | tuple[int, ...],
) -> dict[int, tuple[PrescriptionView, ...]]:
    """Batch-load prescriptions/items for already-authorized record ids."""
    ids = [int(value) for value in clinical_care_record_ids if int(value) > 0]
    if not ids:
        return {}
    rows = list(
        db.exec(
            select(Prescription)
            .where(Prescription.clinical_care_record_id.in_(ids))
            .order_by(
                Prescription.clinical_care_record_id,
                Prescription.created_at,
                Prescription.id,
            )
        ).all()
    )
    views = _views_for_prescriptions(db, rows)
    result: dict[int, list[PrescriptionView]] = {record_id: [] for record_id in ids}
    for view in views:
        result.setdefault(view.clinical_care_record_id, []).append(view)
    return {key: tuple(value) for key, value in result.items()}


def list_current_prescriptions(
    db: Session,
    *,
    clinical_care_record_id: int,
    doctor_user_id: int,
) -> tuple[PrescriptionView, ...]:
    _record_context(
        db,
        clinical_care_record_id=clinical_care_record_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=False,
    )
    rows = list(
        db.exec(
            select(Prescription)
            .where(Prescription.clinical_care_record_id == clinical_care_record_id)
            .order_by(Prescription.created_at, Prescription.id)
        ).all()
    )
    return _views_for_prescriptions(db, rows)


def create_prescription(
    db: Session,
    *,
    clinical_care_record_id: int,
    doctor_user_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
    general_notes: str = "",
    now: datetime | None = None,
) -> PrescriptionView:
    medication, clean_instructions, clean_notes = _validate_item(
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
    )
    clean_general_notes = _validate_general_notes(general_notes)
    record, consultation, _ = _record_context(
        db,
        clinical_care_record_id=clinical_care_record_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    if record.id is None or consultation.id is None:
        raise PrescriptionNotFoundError("O contexto da Prescrição não está persistido.")

    timestamp = _as_utc(now or utc_now())
    prescription = Prescription(
        clinical_care_record_id=record.id,
        consultation_id=consultation.id,
        doctor_user_id=doctor_user_id,
        general_notes=clean_general_notes,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(prescription)
    try:
        db.flush()
        if prescription.id is None:
            raise PrescriptionConflictError("Não foi possível criar a Prescrição.")
        db.add(
            PrescriptionItem(
                prescription_id=prescription.id,
                medication_or_item=medication,
                instructions=clean_instructions,
                notes=clean_notes,
                created_at=timestamp,
                updated_at=timestamp,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PrescriptionConflictError(
            "Não foi possível salvar a Prescrição por conflito concorrente."
        ) from exc

    db.refresh(prescription)
    return _views_for_prescriptions(db, [prescription])[0]


def add_prescription_item(
    db: Session,
    *,
    prescription_id: int,
    doctor_user_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
    now: datetime | None = None,
) -> PrescriptionView:
    medication, clean_instructions, clean_notes = _validate_item(
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
    )
    prescription, _, _, _ = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    timestamp = _as_utc(now or utc_now())
    if prescription.id is None:
        raise PrescriptionNotFoundError("A Prescrição não está persistida.")
    db.add(
        PrescriptionItem(
            prescription_id=prescription.id,
            medication_or_item=medication,
            instructions=clean_instructions,
            notes=clean_notes,
            created_at=timestamp,
            updated_at=timestamp,
        )
    )
    prescription.updated_at = timestamp
    db.add(prescription)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PrescriptionConflictError(
            "Não foi possível adicionar o item por conflito concorrente."
        ) from exc
    db.refresh(prescription)
    return _views_for_prescriptions(db, [prescription])[0]


def update_prescription_item(
    db: Session,
    *,
    prescription_id: int,
    item_id: int,
    doctor_user_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
    now: datetime | None = None,
) -> PrescriptionView:
    medication, clean_instructions, clean_notes = _validate_item(
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
    )
    prescription, _, _, _ = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    item = db.exec(
        select(PrescriptionItem)
        .where(
            PrescriptionItem.id == item_id,
            PrescriptionItem.prescription_id == prescription_id,
        )
        .with_for_update()
    ).first()
    if item is None:
        raise PrescriptionNotFoundError("O item da Prescrição não está disponível.")

    timestamp = _as_utc(now or utc_now())
    item.medication_or_item = medication
    item.instructions = clean_instructions
    item.notes = clean_notes
    item.updated_at = timestamp
    prescription.updated_at = timestamp
    db.add(item)
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return _views_for_prescriptions(db, [prescription])[0]


def remove_prescription_item(
    db: Session,
    *,
    prescription_id: int,
    item_id: int,
    doctor_user_id: int,
    now: datetime | None = None,
) -> PrescriptionView:
    prescription, _, _, _ = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    items = list(
        db.exec(
            select(PrescriptionItem)
            .where(PrescriptionItem.prescription_id == prescription_id)
            .order_by(PrescriptionItem.created_at, PrescriptionItem.id)
            .with_for_update()
        ).all()
    )
    target = next((item for item in items if item.id == item_id), None)
    if target is None:
        raise PrescriptionNotFoundError("O item da Prescrição não está disponível.")
    if len(items) <= 1:
        raise PrescriptionConflictError(
            "A Prescrição precisa manter pelo menos um item. Exclua a Prescrição inteira se necessário."
        )

    prescription.updated_at = _as_utc(now or utc_now())
    db.delete(target)
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return _views_for_prescriptions(db, [prescription])[0]


def update_prescription_notes(
    db: Session,
    *,
    prescription_id: int,
    doctor_user_id: int,
    general_notes: str,
    now: datetime | None = None,
) -> PrescriptionView:
    clean_notes = _validate_general_notes(general_notes)
    prescription, _, _, _ = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    prescription.general_notes = clean_notes
    prescription.updated_at = _as_utc(now or utc_now())
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return _views_for_prescriptions(db, [prescription])[0]


def delete_prescription(
    db: Session,
    *,
    prescription_id: int,
    doctor_user_id: int,
) -> None:
    prescription, _, _, _ = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=True,
        lock=True,
    )
    db.delete(prescription)
    db.commit()


def get_printable_prescription(
    db: Session,
    *,
    prescription_id: int,
    doctor_user_id: int,
) -> PrintablePrescriptionView:
    prescription, record, consultation, professional = _prescription_context(
        db,
        prescription_id=prescription_id,
        doctor_user_id=doctor_user_id,
        editable=False,
        lock=False,
    )
    status = ConsultationStatus(consultation.status)
    if status not in {ConsultationStatus.EM_ANDAMENTO, ConsultationStatus.CONCLUIDA}:
        raise PrescriptionTransitionError(
            "A Prescrição não está disponível para impressão neste estado da Consulta."
        )
    patient = db.get(Patient, record.patient_id)
    if patient is None:
        raise PrescriptionNotFoundError("O paciente da Prescrição não está disponível.")
    view = _views_for_prescriptions(db, [prescription])[0]
    return PrintablePrescriptionView(
        prescription=view,
        patient_name=patient.name,
        professional_name=professional.name,
        registration_identifier=professional.registration_identifier,
        scheduled_at=_as_utc(consultation.scheduled_at),
    )
