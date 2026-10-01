"""Authorization coverage for appointment scheduling application operations."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.appointment_scheduling.application import (
    admin_create_availability_slot,
    admin_list_active_professionals,
    reception_get_agenda,
    reception_list_active_professionals,
)
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.professional_directory.service import create_professional, create_specialty


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _token(db: Session, role: Role, email: str) -> str:
    user = User(email=email, password_hash=hash_password("senha-teste"), role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _professional(db: Session):
    specialty = create_specialty(db, name="Clínica Agenda")
    return create_professional(
        db,
        name="Dra. Agenda",
        registration_identifier="REG-AGENDA",
        specialty_ids=[specialty.id],
    )


def test_admin_and_reception_have_separated_scheduling_permissions(db: Session) -> None:
    professional = _professional(db)
    admin = _token(db, Role.ADMINISTRADOR, "admin-agenda@example.com")
    reception = _token(db, Role.RECEPCIONISTA, "recepcao-agenda@example.com")

    assert len(admin_list_active_professionals(db, token=admin)) == 1
    slot = admin_create_availability_slot(
        db,
        token=admin,
        professional_id=professional.id,
        starts_at_local="2099-01-10T10:00",
    )
    assert slot.id is not None

    assert len(reception_list_active_professionals(db, token=reception)) == 1
    snapshot = reception_get_agenda(
        db,
        token=reception,
        start_date="2099-01-01",
        end_date="2099-01-31",
    )
    assert len(snapshot.slots) == 1

    with pytest.raises(RoleForbiddenError):
        admin_create_availability_slot(
            db,
            token=reception,
            professional_id=professional.id,
            starts_at_local="2099-01-11T10:00",
        )
    with pytest.raises(RoleForbiddenError):
        reception_get_agenda(db, token=admin)


@pytest.mark.parametrize("role", [Role.MEDICO, Role.FINANCEIRO])
def test_doctor_and_finance_cannot_read_schedule_capability(db: Session, role: Role) -> None:
    token = _token(db, role, f"{role.value.casefold()}-agenda@example.com")
    with pytest.raises(RoleForbiddenError):
        admin_list_active_professionals(db, token=token)
    with pytest.raises(RoleForbiddenError):
        reception_list_active_professionals(db, token=token)


def test_missing_session_is_rejected_before_scheduling_data(db: Session) -> None:
    with pytest.raises(AuthenticationRequiredError):
        admin_list_active_professionals(db, token="")
    with pytest.raises(AuthenticationRequiredError):
        reception_get_agenda(db, token="")
