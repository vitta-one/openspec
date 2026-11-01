"""Regressões de nome de funcionário: identidade, autorização e persistência."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, verify_password
from vitta_one.auth.service import create_session
from vitta_one.auth.staff_service import create_receptionist, list_employee_directory
from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.models.auth import User, AuthSession


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine, tables=[User.__table__, AuthSession.__table__])
    with Session(engine) as session:
        yield session
    engine.dispose()


def _session(db: Session, role: Role) -> str:
    user = User(
        email=f"{role.value.lower()}@clinica.example",
        password_hash=hash_password("SenhaDeTeste123!"),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_admin_can_create_named_receptionist_and_directory_shows_name(db):
    token = _session(db, Role.ADMINISTRADOR)
    user = create_receptionist(
        db,
        token=token,
        name="  Maria   de  Souza  ",
        email=" MARIA@EXEMPLO.COM ",
        password="Segura123456789!",
    )
    assert user.display_name == "Maria de Souza"
    assert user.email == "maria@exemplo.com"
    assert user.role == Role.RECEPCIONISTA.value
    assert verify_password(user.password_hash, "Segura123456789!")
    entries = list_employee_directory(db, token=token)
    assert any(row["name"] == "Maria de Souza" for row in entries)


@pytest.mark.parametrize("name", ["", "A", " " * 4, "X" * 161])
def test_rejects_empty_short_or_long_staff_name(db, name):
    token = _session(db, Role.ADMINISTRADOR)
    with pytest.raises(ValueError, match="nome"):
        create_receptionist(
            db,
            token=token,
            name=name,
            email="recepcao@exemplo.com",
            password="Segura123456789!",
        )
    assert db.exec(select(User).where(User.email == "recepcao@exemplo.com")).first() is None


def test_legacy_identity_is_displayed_with_email_fallback(db):
    token = _session(db, Role.ADMINISTRADOR)
    user = User(
        email="legado@exemplo.com",
        password_hash=hash_password("Segura123456789!"),
        role=Role.RECEPCIONISTA.value,
        display_name=None,
    )
    db.add(user)
    db.commit()
    assert user.display_name is None
    entries = list_employee_directory(db, token=token)
    assert any(row["name"] == "legado@exemplo.com" for row in entries)


def test_receptionist_cannot_create_another_receptionist(db):
    token = _session(db, Role.RECEPCIONISTA)
    with pytest.raises(RoleForbiddenError):
        create_receptionist(
            db,
            token=token,
            name="Equipe Teste",
            email="novo@exemplo.com",
            password="Segura123456789!",
        )
