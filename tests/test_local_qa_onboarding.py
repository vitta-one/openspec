"""Real identity and RBAC tests for isolated local QA account onboarding."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import RoleForbiddenError, require_role
from vitta_one.auth.local_qa import (
    LocalQaAccountError, admin_create_qa_receptionist, local_qa_enabled,
    reception_activate_qa_patient,
)
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, verify_password
from vitta_one.auth.service import authenticate_user, create_session
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional
from vitta_one.professional_directory.service import (
    DirectoryConflictError, DirectoryValidationError,
    create_specialty, register_medical_professional,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def qa_env(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://vittaqa:dummy@127.0.0.1:5433/vitta_one_qa",
    )
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "http://localhost:3000")


def identity(db, role, email):
    user = User(email=email, role=role.value, password_hash=hash_password("existing-auth-password"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_qa_gate_fails_closed_without_all_independent_requirements(monkeypatch, qa_env):
    assert local_qa_enabled()
    for name, value in (
        ("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false"),
        ("VITTA_ONE_PUBLIC_URL", "https://clinic.example.com"),
        ("DATABASE_URL", "postgresql+psycopg://x:y@127.0.0.1:5433/production"),
        ("DATABASE_URL", "postgresql+psycopg://x:y@remote.example:5433/vitta_one_qa"),
    ):
        with monkeypatch.context() as mp:
            mp.setenv(name, value)
            assert not local_qa_enabled()


def test_admin_creates_separate_reception_login_with_hashed_password(db, qa_env):
    admin, token = identity(db, Role.ADMINISTRADOR, "admin@example.invalid")
    created = admin_create_qa_receptionist(
        db, token=token, email=" RECEPTION@EXAMPLE.INVALID ",
        password="reception-local-qa-password",
    )
    assert created.role == Role.RECEPCIONISTA.value
    assert created.email == "reception@example.invalid"
    assert created.password_hash != "reception-local-qa-password"
    assert verify_password(created.password_hash, "reception-local-qa-password")
    assert authenticate_user(db, created.email, "reception-local-qa-password").id == created.id
    reception_token = create_session(db, user_id=created.id, ttl=timedelta(hours=1))
    assert require_role(db, reception_token, Role.RECEPCIONISTA).id == created.id
    with pytest.raises(LocalQaAccountError, match="já possui"):
        admin_create_qa_receptionist(
            db, token=token, email=created.email, password="different-password-2026"
        )
    with pytest.raises(LocalQaAccountError, match="12"):
        admin_create_qa_receptionist(db, token=token, email="new@example.invalid", password="short")
    with pytest.raises(RoleForbiddenError):
        admin_create_qa_receptionist(
            db, token=reception_token, email="x@example.invalid", password="new-secure-password"
        )


def test_admin_creates_qa_doctor_linked_to_specialty_without_email(db, qa_env):
    specialty = create_specialty(db, name="Cardiologia")
    result = register_medical_professional(
        db, name="Dra. Teste", email="doctor@example.invalid",
        specialty_ids=[specialty.id], local_qa_password="doctor-local-qa-password",
    )
    assert result.temporary_password is None
    user = db.get(User, result.user_id)
    assert user.role == Role.MEDICO.value
    assert user.must_change_password is False
    assert user.temporary_password_expires_at is None
    assert db.get(Professional, result.professional_id).onboarding_email_status == "NOT_REQUIRED"
    assert authenticate_user(db, user.email, "doctor-local-qa-password").id == user.id
    with pytest.raises(DirectoryConflictError, match="não pode ser redefinida"):
        register_medical_professional(
            db, name="Duplicado", email=user.email,
            specialty_ids=[specialty.id], local_qa_password="other-secure-password",
        )


def test_qa_doctor_password_is_rejected_outside_isolated_local_environment(db, qa_env, monkeypatch):
    specialty = create_specialty(db, name="Clínica Geral")
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false")
    with pytest.raises(DirectoryValidationError, match="QA local"):
        register_medical_professional(
            db, name="Dr. Teste", email="doctor@example.invalid",
            specialty_ids=[specialty.id], local_qa_password="doctor-local-qa-password",
        )
    assert db.exec(select(User)).first() is None


def test_reception_activates_only_consented_registered_patient(db, qa_env):
    admin, admin_token = identity(db, Role.ADMINISTRADOR, "admin@example.invalid")
    receptionist = admin_create_qa_receptionist(
        db, token=admin_token, email="reception@example.invalid",
        password="reception-local-qa-password",
    )
    token = create_session(db, user_id=receptionist.id, ttl=timedelta(hours=1))
    patient = Patient(name="Maria Teste", cpf="52998224725")
    db.add(patient)
    db.commit()
    db.refresh(patient)
    params = dict(
        token=token, patient_id=patient.id, email="patient@example.invalid",
        password="patient-local-qa-password",
    )
    with pytest.raises(LocalQaAccountError, match="consentimento"):
        reception_activate_qa_patient(db, **params, consent_confirmed=False)
    with pytest.raises(RoleForbiddenError):
        reception_activate_qa_patient(
            db, **{**params, "token": admin_token}, consent_confirmed=True
        )
    created = reception_activate_qa_patient(db, **params, consent_confirmed=True)
    assert created.role == Role.PACIENTE.value
    assert db.get(Patient, patient.id).user_id == created.id
    assert authenticate_user(db, created.email, "patient-local-qa-password").id == created.id
    patient_token = create_session(db, user_id=created.id, ttl=timedelta(hours=1))
    assert require_role(db, patient_token, Role.PACIENTE).id == created.id
    with pytest.raises(LocalQaAccountError, match="já possui"):
        reception_activate_qa_patient(db, **params, consent_confirmed=True)
    with pytest.raises(RoleForbiddenError):
        reception_activate_qa_patient(
            db, **{**params, "token": patient_token}, consent_confirmed=True
        )
