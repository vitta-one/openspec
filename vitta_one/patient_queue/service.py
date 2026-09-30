"""Patient registration and reception queue business services."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus


class PatientValidationError(ValueError):
    """Raised when patient input is invalid."""


class PatientAlreadyExistsError(RuntimeError):
    """Raised when a normalized CPF already belongs to a patient."""

    def __init__(self, patient_id: int | None = None) -> None:
        super().__init__("Já existe um paciente cadastrado com esse CPF.")
        self.patient_id = patient_id


class QueueValidationError(ValueError):
    """Raised when queue input is invalid."""


class QueueTransitionError(RuntimeError):
    """Raised when a queue entry cannot perform the requested transition."""


class QueueEmptyError(LookupError):
    """Raised when no waiting patient can be claimed."""


class QueueOwnershipError(PermissionError):
    """Raised when a doctor tries to finish another doctor's active entry."""


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
    """Return only CPF digits; formatting never participates in identity."""
    return re.sub(r"\D", "", str(value or ""))


def is_valid_cpf(value: str) -> bool:
    """Validate Brazilian CPF length, repetition and verifier digits."""
    cpf = normalize_cpf(value)
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


def _parse_priority(value: str | QueuePriority) -> QueuePriority:
    try:
        return value if isinstance(value, QueuePriority) else QueuePriority(str(value))
    except ValueError as exc:
        raise QueueValidationError("Selecione uma prioridade válida.") from exc


def find_patient_by_cpf(db: Session, cpf: str) -> Patient | None:
    """Find a patient by normalized valid CPF without leaking it in errors."""
    normalized = normalize_cpf(cpf)
    if not is_valid_cpf(normalized):
        return None
    return db.exec(select(Patient).where(Patient.cpf == normalized)).first()


def create_patient(db: Session, *, name: str, cpf: str) -> Patient:
    """Create one patient after server-side identity validation."""
    normalized_name = normalize_patient_name(name)
    normalized_cpf = normalize_cpf(cpf)

    if not normalized_name:
        raise PatientValidationError("Informe o nome do paciente.")
    if len(normalized_name) > 160:
        raise PatientValidationError("O nome do paciente excede o limite permitido.")
    if not is_valid_cpf(normalized_cpf):
        raise PatientValidationError("Informe um CPF válido.")

    existing = db.exec(select(Patient).where(Patient.cpf == normalized_cpf)).first()
    if existing is not None:
        raise PatientAlreadyExistsError(existing.id)

    patient = Patient(name=normalized_name, cpf=normalized_cpf)
    db.add(patient)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing = db.exec(select(Patient).where(Patient.cpf == normalized_cpf)).first()
        raise PatientAlreadyExistsError(existing.id if existing else None) from exc
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
    """Place an existing patient in the operational queue."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise QueueValidationError("Selecione um paciente válido.")

    clean_symptoms = str(symptoms or "").strip()
    if not clean_symptoms:
        raise QueueValidationError("Informe os sintomas relatados.")
    if len(clean_symptoms) > 4000:
        raise QueueValidationError("O relato de sintomas excede o limite permitido.")

    parsed_priority = _parse_priority(priority)
    timestamp = _as_utc(now or utc_now())
    entry = QueueEntry(
        patient_id=patient_id,
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


def _to_item(entry: QueueEntry, patient: Patient) -> QueueItem:
    if entry.id is None or patient.id is None:
        raise RuntimeError("Registro de fila sem identificador persistido.")
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
    )


def list_waiting_queue(db: Session) -> list[QueueItem]:
    """Return the active queue in deterministic server-side order."""
    rows = db.exec(
        select(QueueEntry, Patient)
        .join(Patient, Patient.id == QueueEntry.patient_id)
        .where(QueueEntry.status == QueueStatus.AGUARDANDO.value)
        .order_by(_priority_order(), QueueEntry.entered_at, QueueEntry.id)
    ).all()
    return [_to_item(entry, patient) for entry, patient in rows]


def count_waiting_queue(db: Session) -> int:
    """Count active waiting entries without loading sensitive queue payloads."""
    return int(
        db.exec(
            select(func.count(QueueEntry.id)).where(
                QueueEntry.status == QueueStatus.AGUARDANDO.value
            )
        ).one()
    )


def reassess_queue_entry(
    db: Session,
    *,
    entry_id: int,
    symptoms: str,
    priority: str | QueuePriority,
    now: datetime | None = None,
) -> QueueEntry:
    """Update symptoms/priority only while the patient is waiting."""
    entry = db.get(QueueEntry, entry_id)
    if entry is None:
        raise QueueTransitionError("A entrada de fila não está disponível.")
    if entry.status != QueueStatus.AGUARDANDO.value:
        raise QueueTransitionError("Somente pacientes aguardando podem ser reavaliados.")

    clean_symptoms = str(symptoms or "").strip()
    if not clean_symptoms:
        raise QueueValidationError("Informe os sintomas relatados.")
    if len(clean_symptoms) > 4000:
        raise QueueValidationError("O relato de sintomas excede o limite permitido.")

    entry.symptoms = clean_symptoms
    entry.priority = _parse_priority(priority).value
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
    """Logically remove one waiting entry while preserving its history."""
    entry = db.get(QueueEntry, entry_id)
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
    return _to_item(entry, patient)


def claim_next_patient(
    db: Session,
    *,
    doctor_user_id: int,
    now: datetime | None = None,
) -> QueueItem:
    """Atomically claim the first eligible waiting patient for one doctor."""
    doctor = db.exec(
        select(User)
        .where(User.id == doctor_user_id)
        .with_for_update()
    ).first()
    if doctor is None:
        raise QueueValidationError("A identidade médica não está disponível.")

    if get_doctor_active_entry(db, doctor_user_id=doctor_user_id) is not None:
        raise DoctorAlreadyAttendingError(
            "Finalize o atendimento atual antes de chamar outro paciente."
        )

    statement = (
        select(QueueEntry)
        .where(QueueEntry.status == QueueStatus.AGUARDANDO.value)
        .order_by(_priority_order(), QueueEntry.entered_at, QueueEntry.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    entry = db.exec(statement).first()
    if entry is None:
        raise QueueEmptyError("Não há pacientes aguardando.")

    timestamp = _as_utc(now or utc_now())
    entry.status = QueueStatus.EM_ATENDIMENTO.value
    entry.doctor_user_id = doctor_user_id
    entry.called_at = timestamp
    entry.updated_at = timestamp
    db.add(entry)
    db.commit()
    db.refresh(entry)

    patient = db.get(Patient, entry.patient_id)
    if patient is None:
        raise RuntimeError("Paciente associado à fila não foi encontrado.")
    return _to_item(entry, patient)


def finish_queue_entry(
    db: Session,
    *,
    entry_id: int,
    doctor_user_id: int,
    now: datetime | None = None,
) -> QueueEntry:
    """Finish an active attendance only for its assigned doctor."""
    entry = db.exec(
        select(QueueEntry)
        .where(QueueEntry.id == entry_id)
        .with_for_update()
    ).first()
    if entry is None or entry.status != QueueStatus.EM_ATENDIMENTO.value:
        raise QueueTransitionError("O atendimento não está ativo.")
    if entry.doctor_user_id != doctor_user_id:
        raise QueueOwnershipError("O atendimento pertence a outro profissional.")

    timestamp = _as_utc(now or utc_now())
    entry.status = QueueStatus.FINALIZADO.value
    entry.finished_at = timestamp
    entry.updated_at = timestamp
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
