"""Authorization coverage for professional directory application operations."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.professional_directory.application import (
    admin_create_professional,
    admin_create_specialty,
    admin_register_medical_professional,
    admin_list_available_medical_accounts,
    admin_list_professionals,
    admin_list_specialties,
)


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


def _token_for(db: Session, role: Role, email: str) -> str:
    user = User(
        email=email,
        password_hash=hash_password("senha-teste"),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_admin_can_manage_directory(db: Session) -> None:
    admin_token = _token_for(db, Role.ADMINISTRADOR, "admin@example.com")
    specialty = admin_create_specialty(
        db, token=admin_token, name="Cardiologia"
    )
    professional = admin_create_professional(
        db,
        token=admin_token,
        name="Dra. Admin",
        registration_identifier="REG-1",
        specialty_ids=[specialty.id],
        user_id=None,
    )

    assert professional.id is not None
    assert len(admin_list_specialties(db, token=admin_token)) == 1
    assert len(admin_list_professionals(db, token=admin_token)) == 1
    assert admin_list_available_medical_accounts(db, token=admin_token) == []


@pytest.mark.parametrize(
    "role",
    [Role.RECEPCIONISTA, Role.MEDICO, Role.FINANCEIRO],
)
def test_non_admin_roles_cannot_read_or_mutate_directory(
    db: Session, role: Role
) -> None:
    token = _token_for(db, role, f"{role.value.casefold()}@example.com")

    with pytest.raises(RoleForbiddenError):
        admin_list_specialties(db, token=token)
    with pytest.raises(RoleForbiddenError):
        admin_list_professionals(db, token=token)
    with pytest.raises(RoleForbiddenError):
        admin_list_available_medical_accounts(db, token=token)
    with pytest.raises(RoleForbiddenError):
        admin_create_specialty(db, token=token, name="Não permitido")
    with pytest.raises(RoleForbiddenError):
        admin_register_medical_professional(
            db, token=token, name="Dr. Sem Acesso",
            email="medico-nao-autorizado@example.invalid", specialty_ids=[],
        )


def test_missing_and_expired_sessions_are_rejected_before_directory_access(
    db: Session,
) -> None:
    with pytest.raises(AuthenticationRequiredError):
        admin_list_specialties(db, token="")

    admin = User(
        email="expired-admin@example.com",
        password_hash=hash_password("senha-teste"),
        role=Role.ADMINISTRADOR.value,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    expired = create_session(
        db,
        user_id=admin.id,
        ttl=timedelta(minutes=1),
        now=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(AuthenticationRequiredError):
        admin_list_specialties(db, token=expired)
    with pytest.raises(AuthenticationRequiredError):
        admin_create_specialty(db, token=expired, name="Não deve persistir")
