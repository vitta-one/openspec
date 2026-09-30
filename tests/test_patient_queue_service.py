"""Tests for patient identity and reception queue business rules."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.models.auth import User
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus
from vitta_one.patient_queue.service import (
    DoctorAlreadyAttendingError,
    PatientAlreadyExistsError,
    PatientValidationError,
    QueueEmptyError,
    QueueOwnershipError,
    QueueTransitionError,
    claim_next_patient,
    count_waiting_queue,
    create_patient,
    create_queue_entry,
    finish_queue_entry,
    get_doctor_active_entry,
    is_valid_cpf,
    list_waiting_queue,
    normalize_cpf,
    reassess_queue_entry,
    withdraw_queue_entry,
)


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _doctor(db: Session, email: str) -> User:
    user = User(email=email, password_hash="hash-teste", role="MEDICO")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_cpf_normalization_and_validation() -> None:
    assert normalize_cpf("529.982.247-25") == "52998224725"
    assert is_valid_cpf("529.982.247-25") is True
    assert is_valid_cpf("111.111.111-11") is False
    assert is_valid_cpf("529.982.247-24") is False
    assert is_valid_cpf("123") is False


def test_patient_rejects_invalid_and_duplicate_cpf(db: Session) -> None:
    with pytest.raises(PatientValidationError):
        create_patient(db, name="Paciente Teste", cpf="123")

    first = create_patient(db, name="  Paciente   Teste  ", cpf="529.982.247-25")
    assert first.cpf == "52998224725"
    assert first.name == "Paciente Teste"

    with pytest.raises(PatientAlreadyExistsError) as duplicate:
        create_patient(db, name="Outro Nome", cpf="52998224725")
    assert duplicate.value.patient_id == first.id


def test_waiting_queue_orders_priority_then_entry_time_and_id(db: Session) -> None:
    p1 = create_patient(db, name="Verde Antigo", cpf="52998224725")
    p2 = create_patient(db, name="Amarelo", cpf="16899535009")
    p3 = create_patient(db, name="Vermelho Novo", cpf="11144477735")
    p4 = create_patient(db, name="Vermelho Antigo", cpf="93541134780")
    base = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    create_queue_entry(
        db, patient_id=p1.id, symptoms="Sintoma 1", priority="VERDE", now=base
    )
    create_queue_entry(
        db,
        patient_id=p2.id,
        symptoms="Sintoma 2",
        priority="AMARELO",
        now=base + timedelta(minutes=1),
    )
    create_queue_entry(
        db,
        patient_id=p3.id,
        symptoms="Sintoma 3",
        priority="VERMELHO",
        now=base + timedelta(minutes=2),
    )
    create_queue_entry(
        db,
        patient_id=p4.id,
        symptoms="Sintoma 4",
        priority="VERMELHO",
        now=base - timedelta(minutes=1),
    )

    queue = list_waiting_queue(db)
    assert [item.patient_name for item in queue] == [
        "Vermelho Antigo",
        "Vermelho Novo",
        "Amarelo",
        "Verde Antigo",
    ]
    assert [item.priority for item in queue] == [
        QueuePriority.VERMELHO,
        QueuePriority.VERMELHO,
        QueuePriority.AMARELO,
        QueuePriority.VERDE,
    ]



def test_waiting_queue_uses_id_as_final_tiebreaker(db: Session) -> None:
    first_patient = create_patient(db, name="Primeiro", cpf="52998224725")
    second_patient = create_patient(db, name="Segundo", cpf="16899535009")
    moment = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    first = create_queue_entry(
        db,
        patient_id=first_patient.id,
        symptoms="Mesmo horário 1",
        priority="AMARELO",
        now=moment,
    )
    second = create_queue_entry(
        db,
        patient_id=second_patient.id,
        symptoms="Mesmo horário 2",
        priority="AMARELO",
        now=moment,
    )

    queue = list_waiting_queue(db)
    assert [item.id for item in queue] == [first.id, second.id]


def test_wait_time_does_not_mutate_priority(db: Session) -> None:
    patient = create_patient(db, name="Sem Escalonamento", cpf="52998224725")
    entry = create_queue_entry(
        db,
        patient_id=patient.id,
        symptoms="Sintoma estável",
        priority="VERDE",
        now=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    queue = list_waiting_queue(db)
    assert queue[0].id == entry.id
    assert queue[0].priority is QueuePriority.VERDE
    stored = db.get(QueueEntry, entry.id)
    assert stored is not None and stored.priority == QueuePriority.VERDE.value


def test_reassessment_and_withdrawal_only_apply_while_waiting(db: Session) -> None:
    patient = create_patient(db, name="Reavaliado", cpf="52998224725")
    entry = create_queue_entry(
        db, patient_id=patient.id, symptoms="Dor leve", priority="VERDE"
    )

    reassessed = reassess_queue_entry(
        db,
        entry_id=entry.id,
        symptoms="Dor aumentou",
        priority="VERMELHO",
    )
    assert reassessed.priority == QueuePriority.VERMELHO.value

    withdrawn = withdraw_queue_entry(
        db, entry_id=entry.id, reason="Paciente desistiu"
    )
    assert withdrawn.status == QueueStatus.RETIRADO.value
    assert withdrawn.withdrawn_at is not None
    assert withdrawn.withdrawal_reason == "Paciente desistiu"
    assert list_waiting_queue(db) == []

    with pytest.raises(QueueTransitionError):
        reassess_queue_entry(
            db, entry_id=entry.id, symptoms="Outro", priority="AMARELO"
        )
    with pytest.raises(QueueTransitionError):
        withdraw_queue_entry(db, entry_id=entry.id, reason="Outro motivo")


def test_doctor_claim_and_finish_are_owned_and_single_active(db: Session) -> None:
    doctor = _doctor(db, "medico1@exemplo.com")
    other = _doctor(db, "medico2@exemplo.com")
    patient = create_patient(db, name="Atendimento", cpf="52998224725")
    entry = create_queue_entry(
        db, patient_id=patient.id, symptoms="Dor", priority="AMARELO"
    )

    assert count_waiting_queue(db) == 1

    claimed = claim_next_patient(db, doctor_user_id=doctor.id)
    assert claimed.id == entry.id
    assert claimed.status is QueueStatus.EM_ATENDIMENTO
    assert claimed.doctor_user_id == doctor.id
    assert get_doctor_active_entry(db, doctor_user_id=doctor.id) is not None
    assert count_waiting_queue(db) == 0

    with pytest.raises(QueueTransitionError):
        reassess_queue_entry(
            db,
            entry_id=entry.id,
            symptoms="Não pode alterar em atendimento",
            priority="VERMELHO",
        )
    with pytest.raises(QueueTransitionError):
        withdraw_queue_entry(
            db,
            entry_id=entry.id,
            reason="Não pode retirar em atendimento",
        )

    with pytest.raises(DoctorAlreadyAttendingError):
        claim_next_patient(db, doctor_user_id=doctor.id)

    with pytest.raises(QueueOwnershipError):
        finish_queue_entry(db, entry_id=entry.id, doctor_user_id=other.id)

    finished = finish_queue_entry(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
    )
    assert finished.status == QueueStatus.FINALIZADO.value
    assert finished.finished_at is not None
    assert get_doctor_active_entry(db, doctor_user_id=doctor.id) is None

    with pytest.raises(QueueEmptyError):
        claim_next_patient(db, doctor_user_id=doctor.id)
