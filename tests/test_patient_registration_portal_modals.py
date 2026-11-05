"""Regression tests for patient editing and consented portal invitations."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, PatientPortalInvitation
from vitta_one.patient_portal.application import (
    reception_get_patient_portal_status,
    reception_issue_patient_invitation,
)
from vitta_one.patient_portal.service import PatientPortalError
from vitta_one.patient_queue.application import reception_update_patient
from vitta_one.patient_queue.service import PatientValidationError
from vitta_one.professional_directory.email_sender import EmailDelivery


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


def _user(db: Session, role: Role, email: str) -> tuple[User, str]:
    user = User(
        email=email,
        password_hash=hash_password("test-password-for-qa"),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _patient(db: Session, name: str, cpf: str) -> Patient:
    patient = Patient(name=name, cpf=cpf)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_edit_validation_preserves_identity_and_does_not_mutate_on_failure(db):
    _, token = _user(db, Role.RECEPCIONISTA, "edit@example.invalid")
    patient = _patient(db, "Nome original", "52998224725")

    with pytest.raises(PatientValidationError, match="nome"):
        reception_update_patient(
            db, token=token, patient_id=patient.id, name="   ", phone="11999999999"
        )
    with pytest.raises(PatientValidationError, match="telefone"):
        reception_update_patient(
            db, token=token, patient_id=patient.id, name="Nome válido", phone="123"
        )

    db.expire_all()
    current = db.get(Patient, patient.id)
    assert current.name == "Nome original"
    assert current.phone is None
    assert current.cpf == "52998224725"

    updated = reception_update_patient(
        db, token=token, patient_id=patient.id, name="  Nome   editado  ", phone=""
    )
    assert updated.name == "Nome editado"
    assert updated.phone is None
    assert updated.cpf == "52998224725"


def test_reception_permissions_are_checked_for_each_operation(db):
    _, doctor_token = _user(db, Role.MEDICO, "doctor-edit@example.invalid")
    patient = _patient(db, "Paciente QA", "52998224725")
    with pytest.raises(RoleForbiddenError):
        reception_update_patient(
            db, token=doctor_token, patient_id=patient.id, name="Outro nome"
        )
    with pytest.raises(RoleForbiddenError):
        reception_get_patient_portal_status(db, token=doctor_token, patient_id=patient.id)
    with pytest.raises(RoleForbiddenError):
        reception_issue_patient_invitation(
            db,
            token=doctor_token,
            patient_id=patient.id,
            email="qa@example.invalid",
            consent_confirmed=True,
        )
    assert db.exec(select(PatientPortalInvitation)).all() == []


def test_status_reflects_persisted_invitation_and_linked_account(db, monkeypatch):
    _, token = _user(db, Role.RECEPCIONISTA, "status@example.invalid")
    patient = _patient(db, "Paciente QA", "52998224725")
    assert reception_get_patient_portal_status(
        db, token=token, patient_id=patient.id
    ).state == "SEM_PORTAL"

    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    monkeypatch.setattr(
        "vitta_one.patient_portal.service.send_patient_portal_invitation",
        lambda **kwargs: EmailDelivery(status="ACCEPTED", message_id="synthetic"),
    )
    reception_issue_patient_invitation(
        db,
        token=token,
        patient_id=patient.id,
        email=" QA@Example.Invalid ",
        consent_confirmed=True,
    )
    status = reception_get_patient_portal_status(db, token=token, patient_id=patient.id)
    assert status.state == "CONVITE_ENVIADO"
    assert status.email == "qa@example.invalid"

    invitation = db.exec(select(PatientPortalInvitation)).one()
    invitation.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(invitation)
    db.commit()
    assert reception_get_patient_portal_status(
        db, token=token, patient_id=patient.id
    ).state == "CONVITE_EXPIRADO"

    linked, _ = _user(db, Role.PACIENTE, "linked@example.invalid")
    patient.user_id = linked.id
    db.add(patient)
    db.commit()
    active_status = reception_get_patient_portal_status(
        db, token=token, patient_id=patient.id
    )
    assert active_status.state == "ATIVO"
    assert active_status.email == "linked@example.invalid"


def test_invite_blocks_existing_email_and_immediate_replay(db, monkeypatch):
    _, token = _user(db, Role.RECEPCIONISTA, "invite@example.invalid")
    patient = _patient(db, "Paciente A", "52998224725")
    other = _patient(db, "Paciente B", "11144477735")
    _user(db, Role.PACIENTE, "already@example.invalid")
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    sends = []

    def fake_send(**kwargs):
        sends.append(kwargs["email"])
        return EmailDelivery(status="ACCEPTED", message_id="synthetic")

    monkeypatch.setattr(
        "vitta_one.patient_portal.service.send_patient_portal_invitation",
        fake_send,
    )

    with pytest.raises(PatientPortalError, match="vinculado"):
        reception_issue_patient_invitation(
            db, token=token, patient_id=patient.id,
            email="already@example.invalid", consent_confirmed=True,
        )
    with pytest.raises(PatientPortalError, match="consentimento"):
        reception_issue_patient_invitation(
            db, token=token, patient_id=patient.id,
            email="pending@example.invalid", consent_confirmed=False,
        )
    assert sends == []

    reception_issue_patient_invitation(
        db, token=token, patient_id=patient.id,
        email="pending@example.invalid", consent_confirmed=True,
    )
    with pytest.raises(PatientPortalError, match="2 minutos"):
        reception_issue_patient_invitation(
            db, token=token, patient_id=patient.id,
            email="pending@example.invalid", consent_confirmed=True,
        )
    with pytest.raises(PatientPortalError, match="convite"):
        reception_issue_patient_invitation(
            db, token=token, patient_id=other.id,
            email="pending@example.invalid", consent_confirmed=True,
        )
    assert sends == ["pending@example.invalid"]
    assert len(db.exec(select(PatientPortalInvitation)).all()) == 1
    assert db.get(Patient, patient.id).user_id is None


def test_delivery_failure_shows_real_failure_without_account(db, monkeypatch):
    _, token = _user(db, Role.RECEPCIONISTA, "failed@example.invalid")
    patient = _patient(db, "Paciente QA", "52998224725")
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    monkeypatch.setattr(
        "vitta_one.patient_portal.service.send_patient_portal_invitation",
        lambda **kwargs: EmailDelivery(status="FAILED", message_id=None),
    )
    status, delivery = reception_issue_patient_invitation(
        db, token=token, patient_id=patient.id,
        email="failed-user@example.invalid", consent_confirmed=True,
    )
    assert status.state == "FAILED"
    assert delivery.status == "FAILED"
    assert reception_get_patient_portal_status(
        db, token=token, patient_id=patient.id
    ).state == "FALHA_ENVIO"
    assert db.get(Patient, patient.id).user_id is None
