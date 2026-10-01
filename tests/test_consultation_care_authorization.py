"""Authorization coverage for the consultation care lifecycle."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.consultation_care.application import reception_confirm_arrival
from vitta_one.models.auth import User
from vitta_one.patient_queue.service import create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty


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


def _user(db: Session, role: Role, email: str) -> User:
    user = User(email=email, password_hash=hash_password("unit-test-pass"), role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(db: Session, user: User, *, now: datetime | None = None) -> str:
    return create_session(
        db,
        user_id=user.id,
        ttl=timedelta(hours=1),
        now=now,
    )


def _consultation(db: Session) -> int:
    doctor = _user(db, Role.MEDICO, "linked-doctor-care@example.com")
    specialty = create_specialty(db, name="Care Auth")
    professional = create_professional(
        db,
        name="Dra. Care",
        registration_identifier="REG-CARE-AUTH",
        specialty_ids=[specialty.id],
        user_id=doctor.id,
    )
    patient = create_patient(db, name="Paciente Care Auth", cpf="52998224725")
    base = datetime(2099, 1, 1, tzinfo=timezone.utc)
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
    return consultation.id


def test_reception_can_confirm_arrival(db: Session) -> None:
    consultation_id = _consultation(db)
    reception = _user(db, Role.RECEPCIONISTA, "reception-care@example.com")
    token = _token(db, reception)

    entry = reception_confirm_arrival(
        db,
        token=token,
        consultation_id=consultation_id,
        symptoms="Dor",
        priority="VERDE",
    )
    assert entry.consultation_id == consultation_id


@pytest.mark.parametrize("role", [Role.ADMINISTRADOR, Role.MEDICO, Role.FINANCEIRO])
def test_non_reception_roles_are_rejected_before_arrival_lookup(
    db: Session,
    role: Role,
) -> None:
    user = _user(db, role, f"{role.value.casefold()}-care@example.com")
    token = _token(db, user)

    with pytest.raises(RoleForbiddenError):
        reception_confirm_arrival(
            db,
            token=token,
            consultation_id=999999,
            symptoms="Não deve consultar",
            priority="VERDE",
        )


def test_missing_and_expired_sessions_cannot_confirm_arrival(db: Session) -> None:
    with pytest.raises(AuthenticationRequiredError):
        reception_confirm_arrival(
            db,
            token="",
            consultation_id=999999,
            symptoms="Não deve consultar",
            priority="VERDE",
        )

    reception = _user(db, Role.RECEPCIONISTA, "expired-care@example.com")
    expired = _token(
        db,
        reception,
        now=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(AuthenticationRequiredError):
        reception_confirm_arrival(
            db,
            token=expired,
            consultation_id=999999,
            symptoms="Não deve consultar",
            priority="VERDE",
        )
