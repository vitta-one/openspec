"""The Vitta-One emergency queue and scheduled consultations share clinical services.

Tests use synthetic identities only and keep the independent booked pathway intact.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.roles import Role
from vitta_one.clinical_care.service import (
    ClinicalCareNotFoundError,
    get_active_record,
    list_completed_history_for_patient,
    save_active_record,
)
from vitta_one.clinical_prescription.service import (
    PrescriptionAuthorizationError,
    PrescriptionTransitionError,
    create_prescription,
    get_printable_prescription,
    list_current_prescriptions,
)
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.service import (
    DoctorAlreadyAttendingError,
    claim_next_patient,
    create_patient,
    create_queue_entry,
    finish_queue_entry,
)
from vitta_one.professional_directory.service import (
    create_professional,
    create_specialty,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _doctor(db: Session, name: str) -> User:
    doctor = User(
        email=f"walkin-{name}@example.invalid",
        password_hash="hash-for-test-only",
        role=Role.MEDICO.value,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def test_walkin_has_full_clinical_and_prescription_lifecycle(db: Session) -> None:
    doctor = _doctor(db, "responsavel")
    specialty = create_specialty(db, name="Clínica de Urgência")
    professional = create_professional(
        db,
        name="Dra. Urgência",
        registration_identifier="CRM-TEST-EMERGENCY",
        specialty_ids=[specialty.id],
        user_id=doctor.id,
    )
    patient = create_patient(db, name="Paciente Teste", cpf="52998224725")
    entered_at = datetime(2026, 10, 19, 20, tzinfo=timezone.utc)
    entry = create_queue_entry(
        db,
        patient_id=patient.id,
        symptoms="Queixa sintética de teste",
        priority="AMARELO",
        now=entered_at,
    )

    # The initial queue passage is NOT a scheduled consultation.
    assert entry.consultation_id is None
    claimed = claim_next_patient(
        db, doctor_user_id=doctor.id, now=entered_at
    )
    assert claimed.id == entry.id
    assert claimed.consultation_id is None
    assert db.exec(select(Consultation)).all() == []

    record = get_active_record(
        db, entry_id=entry.id, doctor_user_id=doctor.id
    )
    assert record.queue_entry_id == entry.id
    assert record.consultation_id is None

    saved = save_active_record(
        db,
        entry_id=entry.id,
        doctor_user_id=doctor.id,
        chief_complaint="Queixa principal de teste",
        anamnesis="Anamnese de teste",
        diagnosis="Diagnóstico sintético",
        conduct_notes="Conduta sintética",
    )
    assert saved.chief_complaint == "Queixa principal de teste"

    prescription = create_prescription(
        db,
        clinical_care_record_id=record.id,
        doctor_user_id=doctor.id,
        medication_or_item="Medicamento de teste",
        instructions="Posologia fictícia de teste",
    )
    assert prescription.consultation_id is None
    assert len(prescription.items) == 1
    assert len(
        list_current_prescriptions(
            db,
            clinical_care_record_id=record.id,
            doctor_user_id=doctor.id,
        )
    ) == 1

    printable = get_printable_prescription(
        db, prescription_id=prescription.id, doctor_user_id=doctor.id
    )
    assert printable.patient_name == patient.name
    assert printable.professional_name == professional.name
    assert printable.scheduled_at == entered_at

    stranger = _doctor(db, "sem-acesso")
    with pytest.raises(ClinicalCareNotFoundError):
        get_active_record(
            db, entry_id=entry.id, doctor_user_id=stranger.id
        )
    with pytest.raises(PrescriptionAuthorizationError):
        get_printable_prescription(
            db, prescription_id=prescription.id, doctor_user_id=stranger.id
        )
    with pytest.raises(DoctorAlreadyAttendingError):
        claim_next_patient(db, doctor_user_id=doctor.id)

    finish_queue_entry(db, entry_id=entry.id, doctor_user_id=doctor.id)
    assert db.get(QueueEntry, entry.id).status == "FINALIZADO"

    history = list_completed_history_for_patient(db, patient_id=patient.id)
    assert history.total_count == 1
    assert history.items[0].consultation_id is None
    assert history.items[0].diagnosis == "Diagnóstico sintético"
    assert history.items[0].prescriptions[0].id == prescription.id
    assert db.exec(select(ClinicalCareRecord)).one().queue_entry_id == entry.id

    # Completed prescriptions remain printable but cannot be edited.
    assert get_printable_prescription(
        db, prescription_id=prescription.id, doctor_user_id=doctor.id
    ).prescription.id == prescription.id
    with pytest.raises(PrescriptionTransitionError):
        create_prescription(
            db,
            clinical_care_record_id=record.id,
            doctor_user_id=doctor.id,
            medication_or_item="Outro item",
            instructions="Outro texto",
        )


def test_walkin_history_never_shows_active_or_other_patient_records(
    db: Session,
) -> None:
    doctor = _doctor(db, "historico")
    first = create_patient(db, name="Primeiro", cpf="52998224725")
    second = create_patient(db, name="Segundo", cpf="16899535009")
    first_entry = create_queue_entry(
        db, patient_id=first.id, symptoms="Relato A", priority="VERDE"
    )
    second_entry = create_queue_entry(
        db, patient_id=second.id, symptoms="Relato B", priority="VERMELHO"
    )
    claimed = claim_next_patient(db, doctor_user_id=doctor.id)
    assert claimed.id == second_entry.id
    assert list_completed_history_for_patient(db, patient_id=second.id).total_count == 0
    assert list_completed_history_for_patient(db, patient_id=first.id).total_count == 0
    finish_queue_entry(db, entry_id=claimed.id, doctor_user_id=doctor.id)
    assert list_completed_history_for_patient(db, patient_id=second.id).total_count == 1
    assert list_completed_history_for_patient(db, patient_id=first.id).total_count == 0
