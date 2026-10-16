"""Authorization and one-time activation coverage without browser automation."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.appointment_scheduling.application import (
    doctor_get_my_agenda,
    patient_get_my_agenda,
)
from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingValidationError,
    list_consultations,
    reschedule_consultation,
)
from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, verify_password
from vitta_one.auth.service import authenticate_user, create_session
from vitta_one.models.appointment import (
    Consultation,
    ConsultationScheduleChange,
    ProfessionalAvailabilitySlot,
)
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, PatientPortalInvitation
from vitta_one.models.professional import Professional
from vitta_one.patient_portal.application import (
    reception_issue_patient_invitation,
)
from vitta_one.patient_portal.service import (
    PatientPortalActivationError,
    PatientPortalError,
    activate_patient_account,
)
from vitta_one.patient_portal.settings import clinic_location
from vitta_one.patient_queue.application import reception_update_patient
from vitta_one.professional_directory.email_sender import EmailDelivery


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


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


def _user(db: Session, role: Role, email: str) -> User:
    item = User(email=email, password_hash=hash_password("unit-test-password"), role=role.value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _token(db: Session, user: User) -> str:
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _patient(db: Session, *, name: str, cpf: str, user_id: int | None = None) -> Patient:
    item = Patient(name=name, cpf=cpf, user_id=user_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _appointment(db: Session, professional: Professional, patient: Patient, day: int):
    slot = ProfessionalAvailabilitySlot(
        professional_id=professional.id,
        starts_at=datetime(2099, 3, day, 15, tzinfo=timezone.utc),
        status="BOOKED",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    consultation = Consultation(
        patient_id=patient.id,
        professional_id=professional.id,
        availability_slot_id=slot.id,
        scheduled_at=slot.starts_at,
        status=ConsultationStatus.AGENDADA.value,
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation, slot


def test_patient_invite_requires_consent_and_activation_is_one_time(db, monkeypatch):
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    receptionist = _user(db, Role.RECEPCIONISTA, "reception@example.invalid")
    patient = _patient(db, name="Paciente Sintético", cpf="52998224725")
    captured = {}

    def fake_send(**kwargs):
        captured.update(kwargs)
        return EmailDelivery(status="ACCEPTED", message_id="synthetic-message-id")

    monkeypatch.setattr("vitta_one.patient_portal.service.send_patient_portal_invitation", fake_send)
    token = _token(db, receptionist)
    with pytest.raises(PatientPortalError, match="consentimento"):
        reception_issue_patient_invitation(
            db,
            token=token,
            patient_id=patient.id,
            email="person@example.invalid",
            consent_confirmed=False,
        )
    assert db.exec(select(PatientPortalInvitation)).all() == []
    assert db.exec(select(User).where(User.role == Role.PACIENTE.value)).all() == []

    status, delivery = reception_issue_patient_invitation(
        db,
        token=token,
        patient_id=patient.id,
        email=" Person@Example.Invalid ",
        consent_confirmed=True,
    )
    invite = db.exec(select(PatientPortalInvitation)).one()
    assert status.state == "ACCEPTED"
    assert delivery.status == "ACCEPTED"
    assert invite.email == "person@example.invalid"
    assert invite.code_hash != captured["code"]
    assert len(invite.code_hash) == 64
    assert captured["activation_url"] == "https://clinic.example/ativar-paciente"
    assert "/ativar-paciente?" not in captured["activation_url"]
    assert db.get(Patient, patient.id).user_id is None

    activated = activate_patient_account(
        db,
        email="PERSON@example.invalid",
        code=captured["code"],
        password="safe-patient-password-2026",
    )
    assert activated.role == Role.PACIENTE.value
    assert activated.email == "person@example.invalid"
    assert verify_password(activated.password_hash, "safe-patient-password-2026")
    assert db.get(Patient, patient.id).user_id == activated.id
    assert authenticate_user(db, activated.email, "safe-patient-password-2026") is not None
    with pytest.raises(PatientPortalActivationError):
        activate_patient_account(
            db,
            email="person@example.invalid",
            code=captured["code"],
            password="another-safe-password-2026",
        )


def test_expired_invitation_and_duplicate_email_fail_generically(db, monkeypatch):
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    receptionist = _user(db, Role.RECEPCIONISTA, "reception-expired@example.invalid")
    patient = _patient(db, name="Paciente Expirado", cpf="11144477735")
    captured = {}

    def fake_send(**kwargs):
        captured.update(kwargs)
        return EmailDelivery(status="ACCEPTED", message_id="synthetic")

    monkeypatch.setattr("vitta_one.patient_portal.service.send_patient_portal_invitation", fake_send)
    reception_issue_patient_invitation(
        db,
        token=_token(db, receptionist),
        patient_id=patient.id,
        email="expired@example.invalid",
        consent_confirmed=True,
    )
    with pytest.raises(PatientPortalActivationError):
        activate_patient_account(
            db,
            email="expired@example.invalid",
            code=captured["code"],
            password="safe-patient-password-2026",
            now=datetime.now(timezone.utc) + timedelta(hours=25),
        )
    assert db.get(Patient, patient.id).user_id is None


def test_missing_email_configuration_never_activates_portal(db, monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://clinic.example")
    receptionist = _user(db, Role.RECEPCIONISTA, "reception-no-mail@example.invalid")
    patient = _patient(db, name="Paciente Sem E-mail", cpf="11144477735")
    status, delivery = reception_issue_patient_invitation(
        db,
        token=_token(db, receptionist),
        patient_id=patient.id,
        email="pending@example.invalid",
        consent_confirmed=True,
    )
    invitation = db.exec(select(PatientPortalInvitation)).one()
    assert delivery.status == "NOT_CONFIGURED"
    assert status.state == "NOT_CONFIGURED"
    assert invitation.revoked_at is not None
    assert db.get(Patient, patient.id).user_id is None
    with pytest.raises(PatientPortalActivationError):
        activate_patient_account(
            db,
            email=invitation.email,
            code="not-the-code",
            password="safe-patient-password-2026",
        )


def test_reception_operational_update_preserves_portal_link_and_cpf(db):
    receptionist = _user(db, Role.RECEPCIONISTA, "reception-edit@example.invalid")
    patient_user = _user(db, Role.PACIENTE, "linked-patient@example.invalid")
    patient = _patient(db, name="Nome original", cpf="52998224725", user_id=patient_user.id)
    updated = reception_update_patient(
        db,
        token=_token(db, receptionist),
        patient_id=patient.id,
        name="Nome atualizado",
        phone="(11) 98765-4321",
    )
    assert updated.name == "Nome atualizado"
    assert updated.cpf == "52998224725"
    assert updated.user_id == patient_user.id
    assert updated.phone == "11987654321"


def test_clinic_location_never_substitutes_a_fake_address(monkeypatch):
    monkeypatch.delenv("VITTA_ONE_CLINIC_NAME", raising=False)
    monkeypatch.delenv("VITTA_ONE_CLINIC_ADDRESS", raising=False)
    assert clinic_location().configured is False
    monkeypatch.setenv("VITTA_ONE_CLINIC_NAME", "Clínica Sintética")
    monkeypatch.setenv("VITTA_ONE_CLINIC_ADDRESS", "Rua de Teste, 1")
    assert clinic_location().configured is True
    assert clinic_location().address == "Rua de Teste, 1"
    monkeypatch.setenv("VITTA_ONE_CLINIC_ADDRESS", "x" * 501)
    assert clinic_location().configured is False


def test_patient_and_doctor_agendas_are_scoped_to_the_session(db):
    doctor_a = _user(db, Role.MEDICO, "doctor-a@example.invalid")
    doctor_b = _user(db, Role.MEDICO, "doctor-b@example.invalid")
    professional_a = Professional(
        name="Dra. A",
        registration_identifier="REG-PORTAL-A",
        user_id=doctor_a.id,
        is_active=True,
    )
    professional_b = Professional(
        name="Dr. B",
        registration_identifier="REG-PORTAL-B",
        user_id=doctor_b.id,
        is_active=True,
    )
    db.add_all([professional_a, professional_b])
    db.commit()
    db.refresh(professional_a)
    db.refresh(professional_b)
    patient_a_user = _user(db, Role.PACIENTE, "patient-a@example.invalid")
    patient_b_user = _user(db, Role.PACIENTE, "patient-b@example.invalid")
    patient_a = _patient(db, name="Paciente A", cpf="52998224725", user_id=patient_a_user.id)
    patient_b = _patient(db, name="Paciente B", cpf="11144477735", user_id=patient_b_user.id)
    appointment_a, _ = _appointment(db, professional_a, patient_a, 10)
    _appointment(db, professional_b, patient_b, 11)

    own_doctor, doctor_rows = doctor_get_my_agenda(
        db,
        token=_token(db, doctor_a),
        start_date="2099-03-01",
        end_date="2099-03-31",
    )
    own_patient, patient_rows = patient_get_my_agenda(
        db,
        token=_token(db, patient_a_user),
        start_date="2099-03-01",
        end_date="2099-03-31",
    )
    assert own_doctor.id == professional_a.id
    assert [row.patient_id for row in doctor_rows] == [patient_a.id]
    assert own_patient.id == patient_a.id
    assert [row.id for row in patient_rows] == [appointment_a.id]
    assert not hasattr(patient_rows[0], "diagnosis")
    with pytest.raises(RoleForbiddenError):
        patient_get_my_agenda(db, token=_token(db, doctor_a))
    with pytest.raises(TypeError):
        doctor_get_my_agenda(db, token=_token(db, doctor_a), professional_id=professional_b.id)


def test_doctor_without_active_professional_fails_closed(db):
    doctor = _user(db, Role.MEDICO, "unlinked@example.invalid")
    with pytest.raises(SchedulingValidationError, match="associada"):
        doctor_get_my_agenda(db, token=_token(db, doctor))
    professional = Professional(
        name="Profissional inativo",
        registration_identifier="REG-INACTIVE",
        user_id=doctor.id,
        is_active=False,
    )
    db.add(professional)
    db.commit()
    with pytest.raises(SchedulingValidationError, match="associada"):
        doctor_get_my_agenda(db, token=_token(db, doctor))


def test_reschedule_keeps_old_date_and_actor_in_same_record(db):
    receptionist = _user(db, Role.RECEPCIONISTA, "schedule-actor@example.invalid")
    professional = Professional(
        name="Dra. Agenda",
        registration_identifier="REG-HISTORY",
        is_active=True,
    )
    db.add(professional)
    db.commit()
    db.refresh(professional)
    patient = _patient(db, name="Paciente Agenda", cpf="52998224725")
    consultation, old_slot = _appointment(db, professional, patient, 14)
    new_slot = ProfessionalAvailabilitySlot(
        professional_id=professional.id,
        starts_at=datetime(2099, 3, 18, 15, tzinfo=timezone.utc),
        status="AVAILABLE",
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    previous = consultation.scheduled_at
    reschedule_consultation(
        db,
        consultation_id=consultation.id,
        new_slot_id=new_slot.id,
        changed_by_user_id=receptionist.id,
        now=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    event = db.exec(
        select(ConsultationScheduleChange).where(
            ConsultationScheduleChange.consultation_id == consultation.id
        )
    ).one()
    assert event.previous_scheduled_at == previous
    assert event.new_scheduled_at == new_slot.starts_at
    assert event.changed_by_user_id == receptionist.id
    assert list_consultations(db, patient_id=patient.id)[0].schedule_changes
