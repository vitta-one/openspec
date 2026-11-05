"""Consultation arrival-to-care lifecycle business coverage."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingTransitionError,
    cancel_consultation,
    create_availability_slot,
    reschedule_consultation,
    schedule_consultation,
)
from vitta_one.auth.roles import Role
from vitta_one.consultation_care.service import (
    CareLifecycleConflictError,
    CareLifecycleTransitionError,
    CareLifecycleValidationError,
    confirm_arrival,
)
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.domain import QueuePriority, QueueStatus
from vitta_one.patient_queue.service import (
    QueueEmptyError,
    QueueOwnershipError,
    QueueTransitionError,
    claim_next_patient,
    count_waiting_queue,
    create_patient,
    create_queue_entry,
    finish_queue_entry,
    reassess_queue_entry,
    withdraw_queue_entry,
)
from vitta_one.professional_directory.service import (
    create_professional,
    create_specialty,
    set_professional_active,
)


def _cpf(prefix: str) -> str:
    digits = [int(char) for char in prefix]
    first_total = sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1)))
    first = (first_total * 10) % 11
    if first == 10:
        first = 0
    digits.append(first)
    second_total = sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1)))
    second = (second_total * 10) % 11
    if second == 10:
        second = 0
    digits.append(second)
    return "".join(str(digit) for digit in digits)


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


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
    user = User(email=email, password_hash="test-only-hash", role=Role.MEDICO.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _professional(db: Session, *, suffix: str, doctor_user_id: int | None):
    specialty = create_specialty(db, name=f"Especialidade {suffix}")
    return create_professional(
        db,
        name=f"Profissional {suffix}",
        registration_identifier=f"REG-{suffix}",
        specialty_ids=[specialty.id],
        user_id=doctor_user_id,
    )


def _scheduled(
    db: Session,
    *,
    suffix: str,
    patient_prefix: str,
    doctor_user_id: int | None,
    base: datetime,
):
    professional = _professional(
        db,
        suffix=suffix,
        doctor_user_id=doctor_user_id,
    )
    patient = create_patient(
        db,
        name=f"Paciente {suffix}",
        cpf=_cpf(patient_prefix),
    )
    slot = create_availability_slot(
        db,
        professional_id=professional.id,
        starts_at=base + timedelta(days=1),
        now=base,
    )
    consultation = schedule_consultation(
        db,
        patient_id=patient.id,
        slot_id=slot.id,
        now=base,
    )
    return professional, patient, slot, consultation


def test_confirm_arrival_is_atomic_and_preserves_patient(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-arrival@example.com")
    _, patient, slot, consultation = _scheduled(
        db,
        suffix="ARRIVAL",
        patient_prefix="123456789",
        doctor_user_id=doctor.id,
        base=base,
    )

    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor relatada",
        priority="AMARELO",
        now=base + timedelta(hours=1),
    )

    stored = db.get(Consultation, consultation.id)
    assert stored is not None
    assert stored.patient_id == patient.id
    assert stored.status == ConsultationStatus.CONFIRMADA.value
    assert stored.confirmed_at is not None
    assert stored.started_at is None
    assert stored.completed_at is None

    assert entry.patient_id == patient.id
    assert entry.consultation_id == consultation.id
    assert entry.status == QueueStatus.AGUARDANDO.value
    assert entry.priority == QueuePriority.AMARELO.value
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.BOOKED.value



def test_scheduled_arrival_does_not_duplicate_active_walkin(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-active-walkin@example.com")
    _, patient, _, consultation = _scheduled(
        db, suffix="ACTIVE-WALKIN", patient_prefix="246813579",
        doctor_user_id=doctor.id, base=base,
    )
    walkin = create_queue_entry(
        db, patient_id=patient.id, symptoms="Relato inicial", priority="VERDE"
    )
    with pytest.raises(CareLifecycleConflictError, match="entrada ativa"):
        confirm_arrival(
            db, consultation_id=consultation.id,
            symptoms="Outra chegada", priority="AMARELO", now=base,
        )
    assert db.get(Consultation, consultation.id).status == ConsultationStatus.AGENDADA.value
    withdraw_queue_entry(db, entry_id=walkin.id, reason="Saída registrada")
    scheduled_entry = confirm_arrival(
        db, consultation_id=consultation.id,
        symptoms="Chegada após encerramento", priority="VERDE", now=base,
    )
    assert scheduled_entry.patient_id == patient.id
    assert scheduled_entry.consultation_id == consultation.id


@pytest.mark.parametrize(
    ("symptoms", "priority"),
    [
        ("", "VERDE"),
        ("Dor", ""),
        ("Dor", "AZUL"),
    ],
)
def test_invalid_arrival_payload_keeps_consultation_unchanged(
    db: Session,
    symptoms: str,
    priority: str,
) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, f"doctor-invalid-{priority or 'empty'}@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix=f"INVALID-{priority or 'EMPTY'}",
        patient_prefix="987654321",
        doctor_user_id=doctor.id,
        base=base,
    )

    with pytest.raises(CareLifecycleValidationError):
        confirm_arrival(
            db,
            consultation_id=consultation.id,
            symptoms=symptoms,
            priority=priority,
            now=base + timedelta(hours=1),
        )

    stored = db.get(Consultation, consultation.id)
    assert stored is not None
    assert stored.status == ConsultationStatus.AGENDADA.value
    assert stored.confirmed_at is None
    assert db.exec(
        select(QueueEntry).where(QueueEntry.consultation_id == consultation.id)
    ).first() is None


def test_arrival_requires_active_professional_with_medical_account(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-active-check@example.com")
    professional, _, _, consultation = _scheduled(
        db,
        suffix="INACTIVE",
        patient_prefix="246813579",
        doctor_user_id=doctor.id,
        base=base,
    )
    set_professional_active(db, professional_id=professional.id, is_active=False)

    with pytest.raises(CareLifecycleValidationError):
        confirm_arrival(
            db,
            consultation_id=consultation.id,
            symptoms="Dor",
            priority="VERDE",
            now=base + timedelta(hours=1),
        )

    professional2, patient2, slot2, consultation2 = _scheduled(
        db,
        suffix="NO-USER",
        patient_prefix="135792468",
        doctor_user_id=None,
        base=base,
    )
    assert professional2.user_id is None
    assert patient2.id is not None and slot2.id is not None
    with pytest.raises(CareLifecycleValidationError):
        confirm_arrival(
            db,
            consultation_id=consultation2.id,
            symptoms="Dor",
            priority="VERDE",
            now=base + timedelta(hours=1),
        )


def test_repeat_arrival_does_not_duplicate_queue_or_rewrite_timestamp(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-repeat@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix="REPEAT",
        patient_prefix="102938475",
        doctor_user_id=doctor.id,
        base=base,
    )
    first = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Primeiro relato",
        priority="VERDE",
        now=base + timedelta(hours=1),
    )
    first_confirmed = db.get(Consultation, consultation.id).confirmed_at

    with pytest.raises(CareLifecycleTransitionError):
        confirm_arrival(
            db,
            consultation_id=consultation.id,
            symptoms="Segundo relato",
            priority="VERMELHO",
            now=base + timedelta(hours=2),
        )

    stored = db.get(Consultation, consultation.id)
    linked = db.exec(
        select(QueueEntry).where(QueueEntry.consultation_id == consultation.id)
    ).all()
    assert stored is not None and stored.confirmed_at == first_confirmed
    assert len(linked) == 1
    assert linked[0].id == first.id


def test_doctor_eligibility_keeps_walkins_and_hides_other_scheduled_entries(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor1 = _doctor(db, "doctor-one@example.com")
    doctor2 = _doctor(db, "doctor-two@example.com")
    _, _, _, consultation1 = _scheduled(
        db,
        suffix="D1",
        patient_prefix="314159265",
        doctor_user_id=doctor1.id,
        base=base,
    )
    _, _, _, consultation2 = _scheduled(
        db,
        suffix="D2",
        patient_prefix="271828182",
        doctor_user_id=doctor2.id,
        base=base,
    )
    confirm_arrival(
        db,
        consultation_id=consultation1.id,
        symptoms="Consulta D1",
        priority="AMARELO",
        now=base + timedelta(hours=1),
    )
    confirm_arrival(
        db,
        consultation_id=consultation2.id,
        symptoms="Consulta D2",
        priority="AMARELO",
        now=base + timedelta(hours=1),
    )
    walkin = create_patient(db, name="Walk-in", cpf=_cpf("112233445"))
    create_queue_entry(
        db,
        patient_id=walkin.id,
        symptoms="Atendimento avulso",
        priority="VERDE",
        now=base + timedelta(hours=1),
    )

    assert count_waiting_queue(db, doctor_user_id=doctor1.id) == 2
    assert count_waiting_queue(db, doctor_user_id=doctor2.id) == 2


def test_wrong_doctor_cannot_see_or_claim_scheduled_consultation(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    scheduled_doctor = _doctor(db, "scheduled-doctor@example.com")
    other_doctor = _doctor(db, "other-doctor@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix="OWNERSHIP",
        patient_prefix="556677889",
        doctor_user_id=scheduled_doctor.id,
        base=base,
    )
    confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Consulta própria",
        priority="VERMELHO",
        now=base + timedelta(hours=1),
    )

    assert count_waiting_queue(db, doctor_user_id=other_doctor.id) == 0
    with pytest.raises(QueueEmptyError):
        claim_next_patient(
            db,
            doctor_user_id=other_doctor.id,
            now=base + timedelta(hours=2),
        )

    stored = db.get(Consultation, consultation.id)
    assert stored is not None and stored.status == ConsultationStatus.CONFIRMADA.value


def test_claim_and_finish_transition_consultation_with_same_timestamps(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-lifecycle@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix="LIFECYCLE",
        patient_prefix="667788990",
        doctor_user_id=doctor.id,
        base=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor",
        priority="VERMELHO",
        now=base + timedelta(hours=1),
    )

    called_at = base + timedelta(hours=2)
    claimed = claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=called_at,
    )
    active_consultation = db.get(Consultation, consultation.id)
    assert claimed.id == entry.id
    assert claimed.status is QueueStatus.EM_ATENDIMENTO
    assert active_consultation is not None
    assert active_consultation.status == ConsultationStatus.EM_ANDAMENTO.value
    assert active_consultation.started_at == db.get(QueueEntry, entry.id).called_at

    completed_at = base + timedelta(hours=3)
    finished = finish_queue_entry(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
        now=completed_at,
    )
    completed = db.get(Consultation, consultation.id)
    assert finished.status == QueueStatus.FINALIZADO.value
    assert completed is not None
    assert completed.status == ConsultationStatus.CONCLUIDA.value
    assert completed.completed_at == db.get(QueueEntry, entry.id).finished_at

    first_completed = completed.completed_at
    with pytest.raises(QueueTransitionError):
        finish_queue_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            now=base + timedelta(hours=4),
        )
    assert db.get(Consultation, consultation.id).completed_at == first_completed


def test_different_doctor_cannot_finish_scheduled_attendance(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-owner@example.com")
    other = _doctor(db, "doctor-not-owner@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix="FINISH-OWNER",
        patient_prefix="778899001",
        doctor_user_id=doctor.id,
        base=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor",
        priority="VERDE",
        now=base + timedelta(hours=1),
    )
    claim_next_patient(db, doctor_user_id=doctor.id, now=base + timedelta(hours=2))

    with pytest.raises(QueueOwnershipError):
        finish_queue_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=other.id,
            now=base + timedelta(hours=3),
        )
    assert db.get(Consultation, consultation.id).status == ConsultationStatus.EM_ANDAMENTO.value



def test_finish_rejects_inconsistent_consultation_state_without_finishing_queue(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-inconsistent-finish@example.com")
    _, _, _, consultation = _scheduled(
        db,
        suffix="INCONSISTENT-FINISH",
        patient_prefix="515253545",
        doctor_user_id=doctor.id,
        base=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor",
        priority="AMARELO",
        now=base + timedelta(hours=1),
    )
    claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=2),
    )

    stored_consultation = db.get(Consultation, consultation.id)
    stored_consultation.status = ConsultationStatus.CONFIRMADA.value
    db.add(stored_consultation)
    db.commit()

    with pytest.raises(QueueTransitionError):
        finish_queue_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            now=base + timedelta(hours=3),
        )

    queue_entry = db.get(QueueEntry, entry.id)
    consultation_after = db.get(Consultation, consultation.id)
    assert queue_entry.status == QueueStatus.EM_ATENDIMENTO.value
    assert queue_entry.finished_at is None
    assert consultation_after.status == ConsultationStatus.CONFIRMADA.value
    assert consultation_after.completed_at is None


def test_withdraw_scheduled_cancels_consultation_and_releases_or_inactivates_slot(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-withdraw@example.com")
    professional, _, slot, consultation = _scheduled(
        db,
        suffix="WITHDRAW",
        patient_prefix="889900112",
        doctor_user_id=doctor.id,
        base=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor",
        priority="VERDE",
        now=base + timedelta(hours=1),
    )

    withdrawn_at = base + timedelta(hours=2)
    withdrawn = withdraw_queue_entry(
        db,
        entry_id=entry.id,
        reason="Paciente desistiu",
        now=withdrawn_at,
    )
    cancelled = db.get(Consultation, consultation.id)
    assert withdrawn.status == QueueStatus.RETIRADO.value
    assert cancelled is not None
    assert cancelled.status == ConsultationStatus.CANCELADA.value
    assert cancelled.cancelled_at == withdrawn.withdrawn_at
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.AVAILABLE.value

    doctor2 = _doctor(db, "doctor-withdraw-inactive@example.com")
    professional2, _, slot2, consultation2 = _scheduled(
        db,
        suffix="WITHDRAW-INACTIVE",
        patient_prefix="990011223",
        doctor_user_id=doctor2.id,
        base=base,
    )
    entry2 = confirm_arrival(
        db,
        consultation_id=consultation2.id,
        symptoms="Dor",
        priority="AMARELO",
        now=base + timedelta(hours=1),
    )
    set_professional_active(db, professional_id=professional2.id, is_active=False)
    withdraw_queue_entry(
        db,
        entry_id=entry2.id,
        reason="Paciente desistiu",
        now=base + timedelta(hours=2),
    )
    assert db.get(ProfessionalAvailabilitySlot, slot2.id).status == AvailabilitySlotStatus.INACTIVE.value
    assert professional.id is not None


def test_reassessment_preserves_confirmed_consultation_and_scheduling_handlers_reject_it(db: Session) -> None:
    base = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "doctor-reassess@example.com")
    professional, _, _, consultation = _scheduled(
        db,
        suffix="REASSESS",
        patient_prefix="101202303",
        doctor_user_id=doctor.id,
        base=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms="Dor leve",
        priority="VERDE",
        now=base + timedelta(hours=1),
    )
    reassess_queue_entry(
        db,
        entry_id=entry.id,
        symptoms="Dor aumentou",
        priority="VERMELHO",
        now=base + timedelta(hours=2),
    )
    confirmed = db.get(Consultation, consultation.id)
    assert confirmed is not None and confirmed.status == ConsultationStatus.CONFIRMADA.value

    other_slot = create_availability_slot(
        db,
        professional_id=professional.id,
        starts_at=base + timedelta(days=2),
        now=base,
    )
    with pytest.raises(SchedulingTransitionError):
        reschedule_consultation(
            db,
            consultation_id=consultation.id,
            new_slot_id=other_slot.id,
            now=base + timedelta(hours=2),
        )
    with pytest.raises(SchedulingTransitionError):
        cancel_consultation(
            db,
            consultation_id=consultation.id,
            now=base + timedelta(hours=2),
        )


def test_walkin_withdrawal_does_not_touch_consultations(db: Session) -> None:
    patient = create_patient(db, name="Walk-in puro", cpf=_cpf("404505606"))
    entry = create_queue_entry(
        db,
        patient_id=patient.id,
        symptoms="Relato avulso",
        priority="VERDE",
    )
    withdrawn = withdraw_queue_entry(
        db,
        entry_id=entry.id,
        reason="Saiu antes do atendimento",
    )
    assert withdrawn.status == QueueStatus.RETIRADO.value
    assert withdrawn.consultation_id is None
    assert db.exec(select(Consultation)).all() == []
