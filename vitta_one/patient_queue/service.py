"""Patient registration and reception queue business services."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import case, exists, func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.auth.roles import Role
from vitta_one.consultation_care.service import (
    CareLifecycleAssignmentError,
    CareLifecycleConflictError,
    CareLifecycleTransitionError,
    CareLifecycleValidationError,
    cancel_linked_consultation_from_queue,
    complete_linked_consultation,
    start_linked_consultation,
)
from vitta_one.clinical_care.service import (
    ClinicalCareConflictError,
    create_record_for_queue_start,
)
from vitta_one.models.appointment import Consultation
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.active_entry import ActiveQueueEntryError, lock_patient_queue_slot
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus
from vitta_one.patient_queue.validation import (
    QueuePayloadValidationError,
    normalize_queue_symptoms,
    parse_queue_priority,
)


class PatientValidationError(ValueError):
    """Raised when patient input is invalid."""


class PatientAlreadyExistsError(RuntimeError):
    """Raised when a normalized CPF already belongs to a patient."""

    def __init__(self, patient_id: int | None = None) -> None:
        super().__init__("Já existe um paciente cadastrado com esse CPF.")
        self.patient_id = patient_id




@dataclass(frozen=True, slots=True)
class PatientSearchResult:
    """Minimal patient identity shown by the receptionist's quick search."""

    id: int
    name: str
    phone: str | None


def search_patient_identities(
    db: Session, *, query: str, limit: int = 8
) -> list[PatientSearchResult]:
    """Search patient identities without returning CPF or clinical information."""
    if isinstance(limit, bool) or limit < 1 or limit > 20:
        raise PatientValidationError("Limite de busca inválido.")
    value = " ".join(str(query or "").split())[:100]
    if len(value) < 2:
        return []

    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    clauses = [Patient.name.ilike(f"%{escaped}%", escape="\\")]
    digits = re.sub(r"\D", "", value)
    if digits:
        clauses.extend(
            (
                Patient.cpf.like(f"%{digits}%"),
                func.coalesce(Patient.phone, "").like(f"%{digits}%"),
            )
        )
    rows = db.exec(
        select(Patient)
        .where(or_(*clauses))
        .order_by(Patient.name, Patient.id)
        .limit(limit)
    ).all()
    return [
        PatientSearchResult(id=row.id, name=row.name, phone=row.phone)
        for row in rows
        if row.id is not None
    ]


def get_patient_identity(
    db: Session, *, patient_id: int
) -> PatientSearchResult | None:
    """Return the identity fields needed to select a persisted patient."""
    if isinstance(patient_id, bool) or patient_id < 1:
        return None
    patient = db.get(Patient, patient_id)
    if patient is None or patient.id is None:
        return None
    return PatientSearchResult(
        id=patient.id,
        name=patient.name,
        phone=patient.phone,
    )


class QueueValidationError(ValueError):
    """Raised when queue input is invalid."""


class QueueTransitionError(RuntimeError):
    """Raised when a queue entry cannot perform the requested transition."""


class QueueEmptyError(LookupError):
    """Raised when no waiting patient can be claimed."""


class QueueOwnershipError(PermissionError):
    """Raised when a doctor tries to operate another doctor's attendance."""


class DoctorAlreadyAttendingError(RuntimeError):
    """Raised when a doctor already has an active queue attendance."""


@dataclass(frozen=True, slots=True)
class QueueItem:
    """Sanitized queue projection used by application/state layers."""

    id: int
    patient_id: int
    patient_name: str
    symptoms: str
    priority: QueuePriority
    status: QueueStatus
    entered_at: datetime
    doctor_user_id: int | None = None
    called_at: datetime | None = None
    consultation_id: int | None = None
    scheduled_at: datetime | None = None
    professional_name: str | None = None


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_patient_name(value: str) -> str:
    """Collapse whitespace while preserving the patient's written name."""
    return " ".join(str(value or "").strip().split())


def normalize_cpf(value: str) -> str:
    """Normalize a CPF while preserving the exact input grammar for validation."""
    return re.sub(r"\D", "", str(value or ""))


def normalize_patient_phone(value: str | None) -> str | None:
    """Normalize an optional Brazilian contact number to digits only."""
    original = str(value or "").strip()
    if not original:
        return None
    if re.fullmatch(r"[0-9()+.\s-]+", original) is None:
        raise PatientValidationError("Informe um telefone com números, DDD e pontuação válida.")
    digits = re.sub(r"\D", "", original)
    if len(digits) not in (10, 11):
        raise PatientValidationError(
            "Informe um telefone com DDD e 10 ou 11 dígitos."
        )
    return digits


def is_valid_cpf(value: str) -> bool:
    """Validate Brazilian CPF length, repetition and verifier digits."""
    original = str(value or "").strip()
    if re.fullmatch(r"[0-9.\s-]+", original) is None:
        return False
    cpf = normalize_cpf(original)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    digits = [int(char) for char in cpf]

    first_total = sum(
        digit * weight for digit, weight in zip(digits[:9], range(10, 1, -1))
    )
    first = (first_total * 10) % 11
    if first == 10:
        first = 0
    if first != digits[9]:
        return False

    second_total = sum(
        digit * weight for digit, weight in zip(digits[:10], range(11, 1, -1))
    )
    second = (second_total * 10) % 11
    if second == 10:
        second = 0
    return second == digits[10]


def _validated_symptoms(value: str) -> str:
    try:
        return normalize_queue_symptoms(value)
    except QueuePayloadValidationError as exc:
        raise QueueValidationError(str(exc)) from exc


def _validated_priority(value: str | QueuePriority) -> QueuePriority:
    try:
        return parse_queue_priority(value)
    except QueuePayloadValidationError as exc:
        raise QueueValidationError(str(exc)) from exc


def find_patient_by_cpf(db: Session, cpf: str) -> Patient | None:
    """Find a patient by normalized valid CPF without leaking it in errors."""
    normalized = normalize_cpf(cpf)
    if not is_valid_cpf(normalized):
        return None
    return db.exec(select(Patient).where(Patient.cpf == normalized)).first()


def create_patient(
    db: Session, *, name: str, cpf: str, phone: str | None = None
) -> Patient:
    """Create one patient after server-side identity and contact validation."""
    normalized_name = normalize_patient_name(name)
    normalized_cpf = normalize_cpf(cpf)
    normalized_phone = normalize_patient_phone(phone)

    if not normalized_name:
        raise PatientValidationError("Informe o nome do paciente.")
    if len(normalized_name) > 160:
        raise PatientValidationError("O nome do paciente excede o limite permitido.")
    if not is_valid_cpf(normalized_cpf):
        raise PatientValidationError("Informe um CPF válido.")

    existing = db.exec(select(Patient).where(Patient.cpf == normalized_cpf)).first()
    if existing is not None:
        raise PatientAlreadyExistsError(existing.id)

    patient = Patient(
        name=normalized_name, cpf=normalized_cpf, phone=normalized_phone
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.exec(select(Patient).where(Patient.cpf == normalized_cpf)).first()
        raise PatientAlreadyExistsError(existing.id if existing else None) from exc
    db.refresh(patient)
    return patient


def update_patient(
    db: Session, *, patient_id: int, name: str, phone: str | None = None
) -> Patient:
    """Update only the operational name and phone; CPF and portal link stay fixed."""
    normalized_name = normalize_patient_name(name)
    normalized_phone = normalize_patient_phone(phone)
    if not normalized_name:
        raise PatientValidationError("Informe o nome do paciente.")
    if len(normalized_name) > 160:
        raise PatientValidationError("O nome do paciente excede o limite permitido.")
    patient = db.exec(
        select(Patient).where(Patient.id == patient_id).with_for_update()
    ).first()
    if patient is None:
        raise PatientValidationError("O cadastro do paciente não está disponível.")
    patient.name = normalized_name
    patient.phone = normalized_phone
    patient.updated_at = utc_now()
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def create_queue_entry(
    db: Session,
    *,
    patient_id: int,
    symptoms: str,
    priority: str | QueuePriority,
    now: datetime | None = None,
) -> QueueEntry:
    """Place an existing patient in the operational queue as a walk-in."""
    try:
        patient = lock_patient_queue_slot(db, patient_id=patient_id)
    except ActiveQueueEntryError as exc:
        raise QueueValidationError(str(exc)) from exc
    if patient is None:
        raise QueueValidationError("Selecione um paciente válido.")

    clean_symptoms = _validated_symptoms(symptoms)
    parsed_priority = _validated_priority(priority)
    timestamp = _as_utc(now or utc_now())
    entry = QueueEntry(
        patient_id=patient_id,
        consultation_id=None,
        symptoms=clean_symptoms,
        priority=parsed_priority.value,
        status=QueueStatus.AGUARDANDO.value,
        entered_at=timestamp,
        updated_at=timestamp,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def _priority_order():
    return case(
        (QueueEntry.priority == QueuePriority.VERMELHO.value, 0),
        (QueueEntry.priority == QueuePriority.AMARELO.value, 1),
        (QueueEntry.priority == QueuePriority.VERDE.value, 2),
        else_=3,
    )


def _doctor_eligibility_clause(doctor_user_id: int):
    scheduled_for_doctor = exists().where(
        Consultation.id == QueueEntry.consultation_id,
        Professional.id == Consultation.professional_id,
        Professional.user_id == doctor_user_id,
    )
    return or_(QueueEntry.consultation_id.is_(None), scheduled_for_doctor)


def _to_item(db: Session, entry: QueueEntry, patient: Patient) -> QueueItem:
    if entry.id is None or patient.id is None:
        raise RuntimeError("Registro de fila sem identificador persistido.")

    scheduled_at: datetime | None = None
    professional_name: str | None = None
    if entry.consultation_id is not None:
        consultation = db.get(Consultation, entry.consultation_id)
        if consultation is None:
            raise RuntimeError("Consulta vinculada à fila não foi encontrada.")
        professional = db.get(Professional, consultation.professional_id)
        if professional is None:
            raise RuntimeError("Profissional vinculado à consulta não foi encontrado.")
        scheduled_at = _as_utc(consultation.scheduled_at)
        professional_name = professional.name

    return QueueItem(
        id=entry.id,
        patient_id=patient.id,
        patient_name=patient.name,
        symptoms=entry.symptoms,
        priority=QueuePriority(entry.priority),
        status=QueueStatus(entry.status),
        entered_at=_as_utc(entry.entered_at),
        doctor_user_id=entry.doctor_user_id,
        called_at=_as_utc(entry.called_at) if entry.called_at else None,
        consultation_id=entry.consultation_id,
        scheduled_at=scheduled_at,
        professional_name=professional_name,
    )


def list_waiting_queue(db: Session) -> list[QueueItem]:
    """Return the active reception queue in deterministic server-side order."""
    rows = db.exec(
        select(QueueEntry, Patient)
        .join(Patient, Patient.id == QueueEntry.patient_id)
        .where(QueueEntry.status == QueueStatus.AGUARDANDO.value)
        .order_by(_priority_order(), QueueEntry.entered_at, QueueEntry.id)
    ).all()
    return [_to_item(db, entry, patient) for entry, patient in rows]


def count_waiting_queue(
    db: Session,
    *,
    doctor_user_id: int | None = None,
) -> int:
    """Count waiting entries, optionally restricted to one doctor's eligibility."""
    statement = select(func.count(QueueEntry.id)).where(
        QueueEntry.status == QueueStatus.AGUARDANDO.value
    )
    if doctor_user_id is not None:
        statement = statement.where(_doctor_eligibility_clause(doctor_user_id))
    return int(db.exec(statement).one())


def reassess_queue_entry(
    db: Session,
    *,
    entry_id: int,
    symptoms: str,
    priority: str | QueuePriority,
    now: datetime | None = None,
) -> QueueEntry:
    """Update symptoms/priority only while the patient is waiting."""
    entry = db.exec(
        select(QueueEntry).where(QueueEntry.id == entry_id).with_for_update()
    ).first()
    if entry is None:
        raise QueueTransitionError("A entrada de fila não está disponível.")
    if entry.status != QueueStatus.AGUARDANDO.value:
        raise QueueTransitionError("Somente pacientes aguardando podem ser reavaliados.")

    entry.symptoms = _validated_symptoms(symptoms)
    entry.priority = _validated_priority(priority).value
    entry.updated_at = _as_utc(now or utc_now())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def withdraw_queue_entry(
    db: Session,
    *,
    entry_id: int,
    reason: str,
    now: datetime | None = None,
) -> QueueEntry:
    """Logically remove one waiting entry and cancel a linked confirmed Consultation."""
    entry = db.exec(
        select(QueueEntry).where(QueueEntry.id == entry_id).with_for_update()
    ).first()
    if entry is None:
        raise QueueTransitionError("A entrada de fila não está disponível.")
    if entry.status != QueueStatus.AGUARDANDO.value:
        raise QueueTransitionError("Somente pacientes aguardando podem ser retirados da fila.")

    clean_reason = str(reason or "").strip()
    if not clean_reason:
        raise QueueValidationError("Informe o motivo da retirada.")
    if len(clean_reason) > 300:
        raise QueueValidationError("O motivo da retirada excede o limite permitido.")

    timestamp = _as_utc(now or utc_now())
    if entry.consultation_id is not None:
        try:
            cancel_linked_consultation_from_queue(
                db,
                consultation_id=entry.consultation_id,
                now=timestamp,
            )
        except (CareLifecycleTransitionError, CareLifecycleValidationError) as exc:
            raise QueueTransitionError(str(exc)) from exc

    entry.status = QueueStatus.RETIRADO.value
    entry.withdrawal_reason = clean_reason
    entry.withdrawn_at = timestamp
    entry.updated_at = timestamp
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_doctor_active_entry(db: Session, *, doctor_user_id: int) -> QueueItem | None:
    """Return only the current doctor's active queue attendance."""
    row = db.exec(
        select(QueueEntry, Patient)
        .join(Patient, Patient.id == QueueEntry.patient_id)
        .where(
            QueueEntry.status == QueueStatus.EM_ATENDIMENTO.value,
            QueueEntry.doctor_user_id == doctor_user_id,
        )
        .order_by(QueueEntry.called_at.desc(), QueueEntry.id.desc())
    ).first()
    if row is None:
        return None
    entry, patient = row
    return _to_item(db, entry, patient)


def claim_next_patient(
    db: Session,
    *,
    doctor_user_id: int,
    now: datetime | None = None,
) -> QueueItem:
    """Atomically claim the first waiting entry eligible for this doctor."""
    doctor = db.exec(
        select(User).where(User.id == doctor_user_id).with_for_update()
    ).first()
    if doctor is None or doctor.role != Role.MEDICO.value:
        raise QueueValidationError("A identidade médica não está disponível.")

    if get_doctor_active_entry(db, doctor_user_id=doctor_user_id) is not None:
        raise DoctorAlreadyAttendingError(
            "Finalize o atendimento atual antes de chamar outro paciente."
        )

    entry = db.exec(
        select(QueueEntry)
        .where(
            QueueEntry.status == QueueStatus.AGUARDANDO.value,
            _doctor_eligibility_clause(doctor_user_id),
        )
        .order_by(_priority_order(), QueueEntry.entered_at, QueueEntry.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    ).first()
    if entry is None:
        raise QueueEmptyError("Não há pacientes aguardando para este profissional.")

    timestamp = _as_utc(now or utc_now())
    if entry.consultation_id is not None:
        try:
            start_linked_consultation(
                db,
                consultation_id=entry.consultation_id,
                doctor_user_id=doctor_user_id,
                now=timestamp,
            )
        except CareLifecycleAssignmentError as exc:
            raise QueueOwnershipError(str(exc)) from exc
        except (
            CareLifecycleConflictError,
            CareLifecycleTransitionError,
            CareLifecycleValidationError,
        ) as exc:
            raise QueueTransitionError(str(exc)) from exc

    entry.status = QueueStatus.EM_ATENDIMENTO.value
    entry.doctor_user_id = doctor_user_id
    entry.called_at = timestamp
    entry.updated_at = timestamp
    db.add(entry)
    try:
        if entry.consultation_id is None:
            create_record_for_queue_start(
                db, entry=entry, doctor_user_id=doctor_user_id, now=timestamp
            )
        db.commit()
    except ClinicalCareConflictError as exc:
        db.rollback()
        raise QueueTransitionError(
            "O atendimento já possui registro clínico. Atualize a fila."
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise QueueTransitionError(
            "Não foi possível iniciar o atendimento por conflito concorrente. Atualize a fila e tente novamente."
        ) from exc
    db.refresh(entry)

    patient = db.get(Patient, entry.patient_id)
    if patient is None:
        raise RuntimeError("Paciente associado à fila não foi encontrado.")
    return _to_item(db, entry, patient)


def finish_queue_entry(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    now: datetime | None = None,
) -> QueueEntry:
    """Finish an active attendance only for its assigned doctor."""
    entry = db.exec(
        select(QueueEntry).where(QueueEntry.id == entry_id).with_for_update()
    ).first()
    if entry is None or entry.status != QueueStatus.EM_ATENDIMENTO.value:
        raise QueueTransitionError("O atendimento não está ativo.")
    if entry.doctor_user_id != doctor_user_id:
        raise QueueOwnershipError("O atendimento pertence a outro profissional.")

    timestamp = _as_utc(now or utc_now())
    if entry.consultation_id is not None:
        try:
            complete_linked_consultation(
                db,
                consultation_id=entry.consultation_id,
                doctor_user_id=doctor_user_id,
                now=timestamp,
            )
        except CareLifecycleAssignmentError as exc:
            raise QueueOwnershipError(str(exc)) from exc
        except (CareLifecycleTransitionError, CareLifecycleValidationError) as exc:
            raise QueueTransitionError(str(exc)) from exc

    entry.status = QueueStatus.FINALIZADO.value
    entry.finished_at = timestamp
    entry.updated_at = timestamp
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
