"""Reception patient profile: authorized projection and queue deduplication."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.models.professional import Professional
from vitta_one.patient_queue.application import reception_get_patient_operational_summary
from vitta_one.patient_queue.profile import mask_patient_cpf
from vitta_one.patient_queue.service import (
    QueueValidationError, create_patient, create_queue_entry, withdraw_queue_entry,
)


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _token(db, role, email):
    user = User(email=email, password_hash="hash-fixture", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _consultation(db, patient_id, doctor_id, *, scheduled_at, status):
    slot = ProfessionalAvailabilitySlot(
        professional_id=doctor_id, starts_at=scheduled_at, status="BOOKED",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    consultation = Consultation(
        patient_id=patient_id, professional_id=doctor_id,
        availability_slot_id=slot.id, scheduled_at=scheduled_at, status=status,
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation


def test_mask_patient_cpf_only_exposes_last_five_digits():
    assert mask_patient_cpf("52998224725") == "***.***.247-25"
    assert mask_patient_cpf("123") == "Não informado"


def test_reception_profile_has_persisted_future_past_and_queue_without_clinical_data(db):
    patient = create_patient(
        db, name="Teste Privacidade", cpf="529.982.247-25", phone="11999998888"
    )
    doctor = Professional(name="Dra. Teste", registration_identifier="CRM-TEST-PROFILE")
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    future = _consultation(
        db, patient.id, doctor.id, scheduled_at=datetime(2099, 2, 3, tzinfo=timezone.utc),
        status="AGENDADA",
    )
    past = _consultation(
        db, patient.id, doctor.id, scheduled_at=datetime(2022, 1, 3, tzinfo=timezone.utc),
        status="CONCLUIDA",
    )
    entry = create_queue_entry(
        db, patient_id=patient.id,
        symptoms="Texto clínico altamente reservado", priority="AMARELO",
    )
    token = _token(db, Role.RECEPCIONISTA, "recepcao-perfil@example.com")
    profile = reception_get_patient_operational_summary(
        db, token=token, patient_id=patient.id
    )

    assert profile["name"] == "Teste Privacidade"
    assert profile["cpf_masked"] == "***.***.247-25"
    assert "cpf" not in profile and "user_id" not in profile
    assert [row["id"] for row in profile["upcoming"]] == [future.id]
    assert [row["id"] for row in profile["history"]] == [past.id]
    assert profile["active_queue"]["id"] == entry.id
    assert profile["active_queue"]["priority_label"] == "Amarelo"
    assert "Texto clínico" not in str(profile)
    assert "symptoms" not in str(profile)
    assert "diagnosis" not in str(profile)
    assert "password" not in str(profile)


def test_reception_profile_not_found_and_role_checks(db):
    token = _token(db, Role.RECEPCIONISTA, "reception-auth-profile@example.com")
    doctor_token = _token(db, Role.MEDICO, "doctor-auth-profile@example.com")
    assert reception_get_patient_operational_summary(
        db, token=token, patient_id=999999
    ) is None
    assert reception_get_patient_operational_summary(
        db, token=token, patient_id=-1
    ) is None
    with pytest.raises(RoleForbiddenError):
        reception_get_patient_operational_summary(
            db, token=doctor_token, patient_id=999999
        )
    with pytest.raises(AuthenticationRequiredError):
        reception_get_patient_operational_summary(
            db, token="", patient_id=999999
        )


def test_active_queue_entry_cannot_be_duplicated_but_closed_entry_can_be_reentered(db):
    patient = create_patient(db, name="Fila Única", cpf="16899535009")
    first = create_queue_entry(
        db, patient_id=patient.id, symptoms="Primeiro relato", priority="VERDE"
    )
    with pytest.raises(QueueValidationError, match="entrada ativa"):
        create_queue_entry(
            db, patient_id=patient.id, symptoms="Segundo relato", priority="VERMELHO"
        )
    withdraw_queue_entry(db, entry_id=first.id, reason="Paciente saiu")
    second = create_queue_entry(
        db, patient_id=patient.id, symptoms="Novo atendimento", priority="VERDE"
    )
    assert second.id != first.id
