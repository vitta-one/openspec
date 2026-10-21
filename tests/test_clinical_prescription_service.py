"""Business coverage for structured clinical prescriptions."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.appointment_scheduling.temporal import ensure_utc
from vitta_one.auth.roles import Role
from vitta_one.clinical_care.service import list_history_for_active_entry
from vitta_one.clinical_prescription.service import (
    PrescriptionAuthorizationError,
    PrescriptionConflictError,
    PrescriptionNotFoundError,
    PrescriptionTransitionError,
    PrescriptionValidationError,
    add_prescription_item,
    create_prescription,
    delete_prescription,
    get_printable_prescription,
    list_current_prescriptions,
    remove_prescription_item,
    update_prescription_item,
    update_prescription_notes,
)
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.appointment import Consultation
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_prescription import Prescription, PrescriptionItem
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.domain import QueueStatus
from vitta_one.patient_queue.service import (
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
    digits.append(0 if first == 10 else first)
    second_total = sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1)))
    second = (second_total * 10) % 11
    digits.append(0 if second == 10 else second)
    return "".join(str(digit) for digit in digits)


def _doctor(db: Session, suffix: str) -> User:
    user = User(
        email=f"prescription-{suffix}@example.com",
        password_hash="test-only-hash",
        role=Role.MEDICO.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _professional(db: Session, doctor: User, suffix: str):
    specialty = create_specialty(db, name=f"Prescrição {suffix}")
    return create_professional(
        db,
        name=f"Dra. Prescrição {suffix}",
        registration_identifier=f"CRM-{suffix}",
        specialty_ids=[specialty.id],
        user_id=doctor.id,
    )


def _scheduled(
    db: Session,
    *,
    suffix: str,
    cpf_prefix: str,
    base: datetime,
    doctor: User | None = None,
    professional=None,
    patient=None,
    slot_days: int = 1,
):
    doctor = doctor or _doctor(db, suffix)
    professional = professional or _professional(db, doctor, suffix)
    patient = patient or create_patient(
        db,
        name=f"Paciente {suffix}",
        cpf=_cpf(cpf_prefix),
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
        symptoms="Relato para Prescrição",
        priority="VERDE",
        now=base + timedelta(minutes=5),
    )
    return doctor, professional, patient, consultation, entry


def _start(
    db: Session,
    *,
    suffix: str,
    cpf_prefix: str,
    base: datetime,
    doctor: User | None = None,
    professional=None,
    patient=None,
    slot_days: int = 1,
):
    doctor, professional, patient, consultation, entry = _scheduled(
        db,
        suffix=suffix,
        cpf_prefix=cpf_prefix,
        base=base,
        doctor=doctor,
        professional=professional,
        patient=patient,
        slot_days=slot_days,
    )
    claim_next_patient(
        db,
        doctor_user_id=doctor.id,
        now=base + timedelta(minutes=10),
    )
    record = db.exec(
        select(ClinicalCareRecord).where(
            ClinicalCareRecord.consultation_id == consultation.id
        )
    ).one()
    return doctor, professional, patient, consultation, entry, record


def _create(db: Session, record: ClinicalCareRecord, doctor: User, *, suffix: str = "A"):
    return create_prescription(
        db,
        clinical_care_record_id=record.id,
        doctor_user_id=doctor.id,
        medication_or_item=f"Medicamento {suffix}",
        instructions=f"Orientação {suffix}",
        notes=f"Observação {suffix}",
        general_notes=f"Geral {suffix}",
    )


def test_create_prescription_and_first_item_is_atomic(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, entry, record = _start(
        db, suffix="CREATE", cpf_prefix="123456789", base=base
    )
    before_status = db.get(Consultation, consultation.id).status
    before_entry_status = db.get(QueueEntry, entry.id).status

    created = _create(db, record, doctor)

    assert created.clinical_care_record_id == record.id
    assert created.consultation_id == consultation.id
    assert created.doctor_user_id == doctor.id
    assert len(created.items) == 1
    assert created.items[0].medication_or_item == "Medicamento A"
    assert created.items[0].instructions == "Orientação A"
    assert db.get(Consultation, consultation.id).status == before_status
    assert db.get(QueueEntry, entry.id).status == before_entry_status


@pytest.mark.parametrize(
    ("medication", "instructions"),
    [
        ("", "Tomar conforme orientação"),
        ("Dipirona", ""),
    ],
)
def test_invalid_first_item_does_not_leave_empty_document(
    db: Session,
    medication: str,
    instructions: str,
) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix=f"INVALID-{len(medication)}-{len(instructions)}", cpf_prefix="987654321", base=base
    )
    with pytest.raises(PrescriptionValidationError):
        create_prescription(
            db,
            clinical_care_record_id=record.id,
            doctor_user_id=doctor.id,
            medication_or_item=medication,
            instructions=instructions,
        )
    assert db.exec(
        select(Prescription).where(Prescription.clinical_care_record_id == record.id)
    ).all() == []


def test_multiple_prescriptions_and_multiple_items_are_supported(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="MULTI", cpf_prefix="246813579", base=base
    )
    first = _create(db, record, doctor, suffix="1")
    second = _create(db, record, doctor, suffix="2")
    first_updated = add_prescription_item(
        db,
        prescription_id=first.id,
        doctor_user_id=doctor.id,
        medication_or_item="Segundo item",
        instructions="Segunda orientação",
    )

    current = list_current_prescriptions(
        db,
        clinical_care_record_id=record.id,
        doctor_user_id=doctor.id,
    )
    assert [item.id for item in current] == [first.id, second.id]
    assert len(first_updated.items) == 2
    assert [item.medication_or_item for item in first_updated.items] == [
        "Medicamento 1",
        "Segundo item",
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("medication", "x" * 301),
        ("instructions", "x" * 2001),
        ("notes", "x" * 2001),
        ("general_notes", "x" * 4001),
    ],
)
def test_text_limits_reject_without_echoing_sensitive_payload(
    db: Session,
    field: str,
    value: str,
) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db,
        suffix=f"LIMIT-{field}",
        cpf_prefix={
            "medication": "135792468",
            "instructions": "314159265",
            "notes": "271828182",
            "general_notes": "112233445",
        }[field],
        base=base,
    )
    kwargs = {
        "medication_or_item": "Item seguro",
        "instructions": "Orientação segura",
        "notes": "",
        "general_notes": "",
    }
    if field == "medication":
        kwargs["medication_or_item"] = value
    elif field == "instructions":
        kwargs["instructions"] = value
    elif field == "notes":
        kwargs["notes"] = value
    else:
        kwargs["general_notes"] = value

    with pytest.raises(PrescriptionValidationError) as exc_info:
        create_prescription(
            db,
            clinical_care_record_id=record.id,
            doctor_user_id=doctor.id,
            **kwargs,
        )
    assert value not in str(exc_info.value)


def test_edit_item_requires_item_belonging_to_prescription(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="BELONGS", cpf_prefix="223344556", base=base
    )
    first = _create(db, record, doctor, suffix="A")
    second = _create(db, record, doctor, suffix="B")
    foreign_item_id = second.items[0].id

    with pytest.raises(PrescriptionNotFoundError):
        update_prescription_item(
            db,
            prescription_id=first.id,
            item_id=foreign_item_id,
            doctor_user_id=doctor.id,
            medication_or_item="Tentativa",
            instructions="Tentativa",
        )


def test_edit_item_and_general_notes_update_only_prescription_data(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, entry, record = _start(
        db, suffix="EDIT", cpf_prefix="334455667", base=base
    )
    created = _create(db, record, doctor)
    started_at = db.get(Consultation, consultation.id).started_at
    called_at = db.get(QueueEntry, entry.id).called_at

    edited = update_prescription_item(
        db,
        prescription_id=created.id,
        item_id=created.items[0].id,
        doctor_user_id=doctor.id,
        medication_or_item="Item editado",
        instructions="Orientação editada",
        notes="Nota editada",
    )
    noted = update_prescription_notes(
        db,
        prescription_id=created.id,
        doctor_user_id=doctor.id,
        general_notes="Observação geral atualizada",
    )

    assert edited.items[0].medication_or_item == "Item editado"
    assert noted.general_notes == "Observação geral atualizada"
    assert db.get(Consultation, consultation.id).started_at == started_at
    assert db.get(QueueEntry, entry.id).called_at == called_at


def test_remove_item_requires_at_least_one_remaining(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="REMOVE", cpf_prefix="445566778", base=base
    )
    created = _create(db, record, doctor)
    with pytest.raises(PrescriptionConflictError):
        remove_prescription_item(
            db,
            prescription_id=created.id,
            item_id=created.items[0].id,
            doctor_user_id=doctor.id,
        )

    with_second = add_prescription_item(
        db,
        prescription_id=created.id,
        doctor_user_id=doctor.id,
        medication_or_item="Segundo",
        instructions="Segunda orientação",
    )
    after = remove_prescription_item(
        db,
        prescription_id=created.id,
        item_id=with_second.items[0].id,
        doctor_user_id=doctor.id,
    )
    assert len(after.items) == 1
    assert after.items[0].medication_or_item == "Segundo"


def test_delete_prescription_removes_items_during_active_care(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="DELETE", cpf_prefix="556677889", base=base
    )
    created = _create(db, record, doctor)
    item_ids = [item.id for item in created.items]

    delete_prescription(
        db,
        prescription_id=created.id,
        doctor_user_id=doctor.id,
    )

    assert db.get(Prescription, created.id) is None
    for item_id in item_ids:
        assert db.get(PrescriptionItem, item_id) is None


def test_completed_consultation_makes_prescription_immutable_but_printable(
    db: Session,
) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, professional, patient, consultation, entry, record = _start(
        db, suffix="COMPLETE", cpf_prefix="667788990", base=base
    )
    created = _create(db, record, doctor)
    finish_queue_entry(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=1),
    )

    with pytest.raises(PrescriptionTransitionError):
        update_prescription_notes(
            db,
            prescription_id=created.id,
            doctor_user_id=doctor.id,
            general_notes="Não pode",
        )
    with pytest.raises(PrescriptionTransitionError):
        delete_prescription(
            db,
            prescription_id=created.id,
            doctor_user_id=doctor.id,
        )

    printable = get_printable_prescription(
        db,
        prescription_id=created.id,
        doctor_user_id=doctor.id,
    )
    assert printable.patient_name == patient.name
    assert printable.professional_name == professional.name
    assert printable.registration_identifier == professional.registration_identifier
    assert printable.prescription.id == created.id
    assert printable.scheduled_at == ensure_utc(consultation.scheduled_at)


@pytest.mark.parametrize(
    "status",
    [
        ConsultationStatus.AGENDADA.value,
        ConsultationStatus.CONFIRMADA.value,
        ConsultationStatus.CANCELADA.value,
    ],
)
def test_mutation_rejects_any_non_active_consultation_state(
    db: Session,
    status: str,
) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, consultation, _, record = _start(
        db,
        suffix=f"STATE-{status}",
        cpf_prefix={
            ConsultationStatus.AGENDADA.value: "606707808",
            ConsultationStatus.CONFIRMADA.value: "707808909",
            ConsultationStatus.CANCELADA.value: "808909010",
        }[status],
        base=base,
    )
    created = _create(db, record, doctor)
    stored = db.get(Consultation, consultation.id)
    stored.status = status
    db.add(stored)
    db.commit()

    with pytest.raises(PrescriptionTransitionError):
        update_prescription_notes(
            db,
            prescription_id=created.id,
            doctor_user_id=doctor.id,
            general_notes="Não pode alterar",
        )


def test_wrong_doctor_cannot_read_or_mutate_prescription(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="OWNER", cpf_prefix="778899001", base=base
    )
    created = _create(db, record, doctor)
    other = _doctor(db, "OTHER")

    with pytest.raises(PrescriptionAuthorizationError):
        get_printable_prescription(
            db,
            prescription_id=created.id,
            doctor_user_id=other.id,
        )
    with pytest.raises(PrescriptionAuthorizationError):
        update_prescription_notes(
            db,
            prescription_id=created.id,
            doctor_user_id=other.id,
            general_notes="Não autorizado",
        )


def test_history_includes_completed_prescriptions_and_current_stays_out(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "HISTORY")
    professional = _professional(db, doctor, "HISTORY")
    patient = create_patient(db, name="Paciente histórico", cpf=_cpf("889900112"))

    _, _, _, completed_consultation, completed_entry, completed_record = _start(
        db,
        suffix="HISTORY-DONE",
        cpf_prefix="990011223",
        base=base,
        doctor=doctor,
        professional=professional,
        patient=patient,
        slot_days=1,
    )
    first = _create(db, completed_record, doctor, suffix="1")
    second = _create(db, completed_record, doctor, suffix="2")
    add_prescription_item(
        db,
        prescription_id=first.id,
        doctor_user_id=doctor.id,
        medication_or_item="Item adicional",
        instructions="Orientação adicional",
    )
    finish_queue_entry(
        db,
        entry_id=completed_entry.id,
        doctor_user_id=doctor.id,
        now=base + timedelta(hours=1),
    )

    _, _, _, current_consultation, current_entry, current_record = _start(
        db,
        suffix="HISTORY-CURRENT",
        cpf_prefix="101202303",
        base=base,
        doctor=doctor,
        professional=professional,
        patient=patient,
        slot_days=2,
    )
    _create(db, current_record, doctor, suffix="CURRENT")

    page = list_history_for_active_entry(
        db,
        entry_id=current_entry.id,
        doctor_user_id=doctor.id,
        page=1,
    )
    assert page.total_count == 1
    assert page.items[0].consultation_id == completed_consultation.id
    assert [item.id for item in page.items[0].prescriptions] == [first.id, second.id]
    assert current_consultation.id != page.items[0].consultation_id


def test_history_without_prescription_returns_empty_collection(db: Session) -> None:
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor = _doctor(db, "EMPTY-HISTORY")
    professional = _professional(db, doctor, "EMPTY-HISTORY")
    patient = create_patient(db, name="Paciente sem prescrição", cpf=_cpf("202303404"))

    _, _, _, _, done_entry, _ = _start(
        db,
        suffix="EMPTY-DONE",
        cpf_prefix="303404505",
        base=base,
        doctor=doctor,
        professional=professional,
        patient=patient,
    )
    finish_queue_entry(db, entry_id=done_entry.id, doctor_user_id=doctor.id)

    _, _, _, _, current_entry, _ = _start(
        db,
        suffix="EMPTY-CURRENT",
        cpf_prefix="404505606",
        base=base,
        doctor=doctor,
        professional=professional,
        patient=patient,
        slot_days=2,
    )

    page = list_history_for_active_entry(
        db,
        entry_id=current_entry.id,
        doctor_user_id=doctor.id,
    )
    assert page.total_count == 1
    assert page.items[0].prescriptions == ()


def test_walkin_receives_clinical_record_without_booked_consultation(db: Session) -> None:
    doctor = _doctor(db, "WALKIN")
    patient = create_patient(db, name="Paciente avulso", cpf=_cpf("505606707"))
    entry = create_queue_entry(
        db,
        patient_id=patient.id,
        symptoms="Walk-in",
        priority="VERDE",
    )
    claimed = claim_next_patient(db, doctor_user_id=doctor.id)
    assert claimed.consultation_id is None
    records = db.exec(select(ClinicalCareRecord)).all()
    assert len(records) == 1
    assert records[0].queue_entry_id == entry.id
    assert records[0].consultation_id is None
    assert db.exec(select(Prescription)).all() == []
    assert db.get(QueueEntry, entry.id).status == QueueStatus.EM_ATENDIMENTO.value


def test_printable_prescription_is_available_to_author_while_consultation_is_active(
    db: Session,
) -> None:
    """17.7: the doctor's active document is readable through the print domain contract."""
    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, professional, patient, consultation, _, record = _start(
        db, suffix="PRINT-ACTIVE", cpf_prefix="606707818", base=base
    )
    created = _create(db, record, doctor)
    printable = get_printable_prescription(
        db, prescription_id=created.id, doctor_user_id=doctor.id
    )
    assert db.get(Consultation, consultation.id).status == ConsultationStatus.EM_ANDAMENTO.value
    assert printable.patient_name == patient.name
    assert printable.professional_name == professional.name
    assert printable.registration_identifier == professional.registration_identifier
    assert printable.scheduled_at == ensure_utc(consultation.scheduled_at)
    assert printable.prescription.id == created.id
    assert printable.prescription.items[0].medication_or_item == "Medicamento A"
    assert printable.prescription.items[0].instructions == "Orientação A"
    assert printable.prescription.general_notes == "Geral A"


def test_database_failure_never_echoes_sensitive_payload_to_functional_error(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """15.3: SQLAlchemy exceptions are sanitized at the prescription service boundary."""
    from sqlalchemy.exc import SQLAlchemyError

    base = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    doctor, _, _, _, _, record = _start(
        db, suffix="DB-ERROR", cpf_prefix="707808919", base=base
    )
    created = _create(db, record, doctor)
    sensitive = "SENSITIVE_MEDICATION_SAMPLE"
    original_rollback = db.rollback
    rollback_calls = []

    def fail_commit() -> None:
        raise SQLAlchemyError(f"constraint violation: {sensitive}")

    def checked_rollback() -> None:
        rollback_calls.append(True)
        original_rollback()

    monkeypatch.setattr(db, "commit", fail_commit)
    monkeypatch.setattr(db, "rollback", checked_rollback)
    with pytest.raises(PrescriptionConflictError) as exc:
        update_prescription_notes(
            db,
            prescription_id=created.id,
            doctor_user_id=doctor.id,
            general_notes=sensitive,
        )
    assert rollback_calls
    assert sensitive not in str(exc.value)
    assert "constraint" not in str(exc.value).lower()
