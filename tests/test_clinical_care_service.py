"""Business and privacy coverage for the clinical care record capability."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.auth.roles import Role
from vitta_one.clinical_care.service import (
    ClinicalCareAuthorizationError,
    ClinicalCareConflictError,
    ClinicalCareNotFoundError,
    ClinicalCareValidationError,
    create_record_for_consultation_start,
    get_active_record,
    list_history_for_active_entry,
    save_active_record,
)
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.appointment import Consultation
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.domain import QueueStatus
from vitta_one.patient_queue.service import (
    QueueTransitionError,
    claim_next_patient,
    create_patient,
    create_queue_entry,
    finish_queue_entry,
)
from vitta_one.professional_directory.service import create_professional, create_specialty


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


def _doctor(db: Session, suffix: str) -> User:
    user = User(
        email=f"doctor-{suffix}@example.com",
        password_hash="test-only-hash",
        role=Role.MEDICO.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _professional(db: Session, *, suffix: str, doctor_user_id: int):
    specialty = create_specialty(db, name=f"Especialidade Clínica {suffix}")
    return create_professional(
        db,
        name=f"Profissional {suffix}",
        registration_identifier=f"REG-CLIN-{suffix}",
        specialty_ids=[specialty.id],
        user_id=doctor_user_id,
    )


def _scheduled(
    db: Session,
    *,
    suffix: str,
    patient_prefix: str,
    base: datetime,
    doctor: User | None = None,
    patient=None,
    professional=None,
    slot_days: int = 1,
):
    doctor = doctor or _doctor(db, suffix)
    professional = professional or _professional(
        db,
        suffix=suffix,
        doctor_user_id=doctor.id,
    )
    patient = patient or create_patient(
        db,
        name=f"Paciente {suffix}",
        cpf=_cpf(patient_prefix),
    )
    slot = create_availability_slot(
        db,
        professional_id=professional.id,
        starts_at=base + timedelta(days=slot_days),
        now=base,
    )
    consultation = schedule_consultation(
        db,
        patient_id=patient.id,
        slot_id=slot.id,
        now=base,
    )
    entry = confirm_arrival(
        db,
        consultation_id=consultation.id,
        symptoms=f"Relato {suffix}",
        priority="VERDE",
        now=base + timedelta(minutes=10),
    )
    return doctor, professional, patient, consultation, entry


def _start(
    db: Session,
    *,
    suffix: str,
    patient_prefix: str,
    base: datetime,
):
    doctor, professional, patient, consultation, entry = _scheduled(
        db,
        suffix=suffix,
        patient_prefix=patient_prefix,
        base=base,
    )
    claimed = claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=base + timedelta(minutes=20),
    )
    return doctor, professional, patient, consultation, entry, claimed


def test_scheduled_claim_creates_exactly_one_empty_record(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, patient, consultation, _, claimed = _start(
        db,
        suffix="CREATE",
        patient_prefix="123456789",
        base=base,
    )

    record = db.exec(
        select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    ).one()

    assert claimed.consultation_id == consultation.id
    assert record.patient_id == patient.id
    assert record.doctor_user_id == doctor.id
    assert record.chief_complaint == ""
    assert record.anamnesis == ""
    assert record.diagnosis == ""
    assert record.conduct_notes == ""


def test_walkin_claim_does_not_create_clinical_record(db: Session) -> None:
    doctor = _doctor(db, "WALKIN")
    patient = create_patient(db, name="Paciente avulso", cpf=_cpf("987654321"))
    create_queue_entry(
        db,
        patient_id=patient.id,
        symptoms="Atendimento avulso",
        priority="VERDE",
    )

    item = claim_next_patient(db, doctor_user_id=doctor.id)
    assert item.consultation_id is None
    assert db.exec(select(ClinicalCareRecord)).all() == []


def test_duplicate_record_is_rejected_and_claim_rolls_back(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, entry = _scheduled(
        db,
        suffix="DUPLICATE",
        patient_prefix="246813579",
        base=base,
    )
    create_record_for_consultation_start(
        db,
        consultation=consultation,
        doctor_user_id=doctor.id,
        now=base + timedelta(minutes=15),
    )
    db.commit()

    with pytest.raises(QueueTransitionError):
        claim_next_patient(
            db,
            doctor_user_id=doctor.id,
            now=base + timedelta(minutes=20),
        )

    stored_entry = db.get(QueueEntry, entry.id)
    stored_consultation = db.get(Consultation, consultation.id)
    records = db.exec(
        select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    ).all()
    assert stored_entry.status == QueueStatus.AGUARDANDO.value
    assert stored_entry.doctor_user_id is None
    assert stored_consultation.status == ConsultationStatus.CONFIRMADA.value
    assert stored_consultation.started_at is None
    assert len(records) == 1


def test_database_unique_constraint_blocks_second_record(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, _ = _scheduled(
        db,
        suffix="UNIQUE",
        patient_prefix="135792468",
        base=base,
    )
    create_record_for_consultation_start(
        db,
        consultation=consultation,
        doctor_user_id=doctor.id,
        now=base,
    )
    db.commit()

    duplicate = ClinicalCareRecord(
        consultation_id=consultation.id,
        patient_id=consultation.patient_id,
        doctor_user_id=doctor.id,
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_partial_save_allows_empty_fields_and_preserves_lifecycle(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, entry, _ = _start(
        db,
        suffix="PARTIAL",
        patient_prefix="314159265",
        base=base,
    )
    before_consultation = db.get(Consultation, consultation.id)
    before_entry = db.get(QueueEntry, entry.id)
    started_at = before_consultation.started_at
    called_at = before_entry.called_at

    saved = save_active_record(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
        chief_complaint="  Cefaleia há dois dias  ",
        anamnesis="",
        diagnosis="",
        conduct_notes="Orientações gerais",
        now=base + timedelta(minutes=30),
    )

    assert saved.chief_complaint == "Cefaleia há dois dias"
    assert saved.anamnesis == ""
    assert saved.diagnosis == ""
    assert saved.conduct_notes == "Orientações gerais"

    after_consultation = db.get(Consultation, consultation.id)
    after_entry = db.get(QueueEntry, entry.id)
    assert after_consultation.status == ConsultationStatus.EM_ANDAMENTO.value
    assert after_consultation.started_at == started_at
    assert after_entry.status == QueueStatus.EM_ATENDIMENTO.value
    assert after_entry.called_at == called_at


@pytest.mark.parametrize(
    ("field", "limit"),
    [
        ("chief_complaint", 4000),
        ("anamnesis", 12000),
        ("diagnosis", 6000),
        ("conduct_notes", 8000),
    ],
)
def test_server_limits_reject_oversized_content_without_echo(
    db: Session,
    field: str,
    limit: int,
) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, entry, _ = _start(
        db,
        suffix=f"LIMIT-{field}",
        patient_prefix={
            "chief_complaint": "112233445",
            "anamnesis": "223344556",
            "diagnosis": "334455667",
            "conduct_notes": "445566778",
        }[field],
        base=base,
    )
    secret_payload = "SENSITIVE-" + ("x" * limit)
    values = {
        "chief_complaint": "",
        "anamnesis": "",
        "diagnosis": "",
        "conduct_notes": "",
    }
    values[field] = secret_payload

    with pytest.raises(ClinicalCareValidationError) as exc_info:
        save_active_record(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            **values,
        )
    assert secret_payload not in str(exc_info.value)


def test_wrong_doctor_cannot_read_or_write_current_record(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, entry, _ = _start(
        db,
        suffix="OWNER",
        patient_prefix="556677889",
        base=base,
    )
    other = _doctor(db, "OTHER")

    with pytest.raises(ClinicalCareNotFoundError):
        get_active_record(
            db,
            entry_id=entry.id,
            doctor_user_id=other.id,
        )
    with pytest.raises(ClinicalCareNotFoundError):
        save_active_record(
            db,
            entry_id=entry.id,
            doctor_user_id=other.id,
            chief_complaint="Não autorizado",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
        )
    assert doctor.id != other.id


def test_concluded_record_is_immutable_but_empty_record_can_be_concluded(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, entry, _ = _start(
        db,
        suffix="FINAL",
        patient_prefix="667788990",
        base=base,
    )
    record_before = db.exec(
        select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    ).one()
    assert record_before.chief_complaint == ""

    finish_queue_entry(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=1),
    )
    assert db.get(Consultation, consultation.id).status == ConsultationStatus.CONCLUIDA.value

    with pytest.raises(ClinicalCareNotFoundError):
        save_active_record(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            chief_complaint="Tentativa tardia",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
        )
    record_after = db.get(ClinicalCareRecord, record_before.id)
    assert record_after.chief_complaint == ""


def test_history_contains_only_completed_records_in_descending_order(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "HISTORY")
    professional = _professional(db, suffix="HISTORY", doctor_user_id=doctor.id)
    patient = create_patient(db, name="Paciente histórico", cpf=_cpf("778899001"))

    completed_ids: list[int] = []
    for position in range(3):
        _, _, _, consultation, entry = _scheduled(
            db,
            suffix=f"HIST-{position}",
            patient_prefix="889900112",
            base=base,
            doctor=doctor,
            patient=patient,
            professional=professional,
            slot_days=position + 1,
        )
        claim_next_patient(
            db,
            doctor_user_id=doctor.id,
            now=base + timedelta(minutes=20 + position * 10),
        )
        save_active_record(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            chief_complaint=f"Queixa {position}",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
            now=base + timedelta(minutes=25 + position * 10),
        )
        finish_queue_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            now=base + timedelta(minutes=30 + position * 10),
        )
        completed_ids.append(consultation.id)

    _, _, _, current_consultation, current_entry = _scheduled(
        db,
        suffix="HIST-CURRENT",
        patient_prefix="990011223",
        base=base,
        doctor=doctor,
        patient=patient,
        professional=professional,
        slot_days=5,
    )
    claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=2),
    )

    page = list_history_for_active_entry(
        db,
        entry_id=current_entry.id,
        doctor_user_id=doctor.id,
        page=1,
    )
    assert page.total_count == 3
    assert [item.consultation_id for item in page.items] == list(reversed(completed_ids))
    assert current_consultation.id not in [item.consultation_id for item in page.items]


def test_history_is_server_paginated_at_ten_records(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "PAGING")
    professional = _professional(db, suffix="PAGING", doctor_user_id=doctor.id)
    patient = create_patient(db, name="Paciente paginação", cpf=_cpf("101202303"))

    for position in range(11):
        _, _, _, _, entry = _scheduled(
            db,
            suffix=f"PAGE-{position}",
            patient_prefix="202303404",
            base=base,
            doctor=doctor,
            patient=patient,
            professional=professional,
            slot_days=position + 1,
        )
        claim_next_patient(
            db,
            doctor_user_id=doctor.id,
            now=base + timedelta(hours=position + 1),
        )
        finish_queue_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
            now=base + timedelta(hours=position + 1, minutes=5),
        )

    _, _, _, _, current_entry = _scheduled(
        db,
        suffix="PAGE-CURRENT",
        patient_prefix="303404505",
        base=base,
        doctor=doctor,
        patient=patient,
        professional=professional,
        slot_days=20,
    )
    claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=20),
    )

    first = list_history_for_active_entry(
        db,
        entry_id=current_entry.id,
        doctor_user_id=doctor.id,
        page=1,
    )
    second = list_history_for_active_entry(
        db,
        entry_id=current_entry.id,
        doctor_user_id=doctor.id,
        page=2,
    )
    assert first.total_count == 11
    assert first.total_pages == 2
    assert len(first.items) == 10
    assert len(second.items) == 1


def test_history_requires_active_context_and_never_returns_another_patient(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, entry, _ = _start(
        db,
        suffix="ACTIVE-HISTORY",
        patient_prefix="404505606",
        base=base,
    )
    own_page = list_history_for_active_entry(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
    )
    assert own_page.total_count == 0

    finish_queue_entry(db, entry_id=entry.id, doctor_user_id=doctor.id)
    with pytest.raises(ClinicalCareNotFoundError):
        list_history_for_active_entry(
            db,
            entry_id=entry.id,
            doctor_user_id=doctor.id,
        )


def test_history_loads_prescriptions_only_for_records_on_selected_page(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """17.6: pagination is applied before the prescription batch loader runs."""
    from vitta_one.clinical_care import service as clinical_service

    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "PAGE-PRESCRIPTION")
    professional = _professional(db, suffix="PAGE-PRESCRIPTION", doctor_user_id=doctor.id)
    patient = create_patient(db, name="Paciente paginação prescrição", cpf=_cpf("919101202"))
    for position in range(11):
        _, _, _, _, entry = _scheduled(
            db,
            suffix=f"RX-PAGE-{position}",
            patient_prefix="808909010",
            base=base,
            doctor=doctor,
            patient=patient,
            professional=professional,
            slot_days=position + 1,
        )
        claim_next_patient(
            db, doctor_user_id=doctor.id,
            now=base + timedelta(hours=position + 1),
        )
        finish_queue_entry(
            db, entry_id=entry.id, doctor_user_id=doctor.id,
            now=base + timedelta(hours=position + 1, minutes=5),
        )

    seen_ids: list[tuple[int, ...]] = []
    actual_loader = clinical_service.list_prescriptions_for_records

    def observed_loader(db_session, *, clinical_care_record_ids):
        seen_ids.append(tuple(clinical_care_record_ids))
        return actual_loader(
            db_session, clinical_care_record_ids=clinical_care_record_ids
        )

    monkeypatch.setattr(clinical_service, "list_prescriptions_for_records", observed_loader)
    first = clinical_service.list_completed_history_for_patient(db, patient_id=patient.id, page=1)
    second = clinical_service.list_completed_history_for_patient(db, patient_id=patient.id, page=2)
    assert first.total_count == 11
    assert first.total_pages == 2
    assert len(first.items) == 10
    assert len(second.items) == 1
    assert len(seen_ids) == 2
    assert seen_ids[0] == tuple(item.record_id for item in first.items)
    assert seen_ids[1] == tuple(item.record_id for item in second.items)
    assert set(seen_ids[0]).isdisjoint(seen_ids[1])
