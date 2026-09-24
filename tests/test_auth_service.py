"""Integration-level unit tests for identity, sessions, bootstrap, and RBAC."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import RoleForbiddenError, require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, hash_session_token, verify_password
from vitta_one.auth.service import (
    authenticate_user,
    bootstrap_first_admin,
    create_session,
    resolve_session,
    revoke_session,
)
from vitta_one.models.auth import AuthSession, User


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


def create_user(db: Session, *, email: str, role: Role, password: str = "senha-teste") -> User:
    user = User(email=email, role=role.value, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_login_valid_missing_email_and_wrong_password(db: Session) -> None:
    user = create_user(db, email="medico@exemplo.com", role=Role.MEDICO)

    assert authenticate_user(db, " MEDICO@EXEMPLO.COM ", "senha-teste") == user
    assert authenticate_user(db, "inexistente@exemplo.com", "senha-teste") is None
    assert authenticate_user(db, "medico@exemplo.com", "senha-incorreta") is None
    assert authenticate_user(db, "email-invalido", "senha-teste") is None


def test_session_absent_expired_revoked_and_logout(db: Session) -> None:
    user = create_user(db, email="recepcao@exemplo.com", role=Role.RECEPCIONISTA)
    assert user.id is not None
    now = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)

    assert resolve_session(db, "") is None

    expired_token = create_session(db, user_id=user.id, ttl=timedelta(minutes=5), now=now)
    assert resolve_session(db, expired_token, now=now + timedelta(minutes=6)) is None

    active_token = create_session(db, user_id=user.id, ttl=timedelta(hours=1), now=now)
    identity = resolve_session(db, active_token, now=now + timedelta(minutes=1))
    assert identity is not None
    assert identity.role is Role.RECEPCIONISTA

    assert revoke_session(db, active_token, now=now + timedelta(minutes=2)) is True
    assert resolve_session(db, active_token, now=now + timedelta(minutes=3)) is None

    stored = db.exec(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(active_token))
    ).first()
    assert stored is not None
    assert active_token != stored.token_hash


@pytest.mark.parametrize("role", list(Role))
def test_each_role_is_authorized_only_for_its_own_shell(db: Session, role: Role) -> None:
    user = create_user(db, email=f"{role.value.casefold()}@exemplo.com", role=role)
    assert user.id is not None
    token = create_session(db, user_id=user.id, ttl=timedelta(hours=1))

    identity = require_role(db, token, role)
    assert identity.role is role

    another_role = next(candidate for candidate in Role if candidate is not role)
    with pytest.raises(RoleForbiddenError):
        require_role(db, token, another_role)


def test_bootstrap_is_idempotent_and_does_not_overwrite_existing_password(db: Session) -> None:
    first = bootstrap_first_admin(
        db,
        email="ADMIN@EXEMPLO.COM",
        password="senha-original",
    )
    assert first.created is True

    admin = db.exec(select(User).where(User.id == first.user_id)).one()
    original_hash = admin.password_hash
    assert verify_password(original_hash, "senha-original") is True

    repeated = bootstrap_first_admin(
        db,
        email="admin@exemplo.com",
        password="senha-nova-que-nao-deve-substituir",
    )
    assert repeated.created is False
    assert repeated.user_id == first.user_id

    admins = db.exec(
        select(User).where(User.role == Role.ADMINISTRADOR.value)
    ).all()
    assert len(admins) == 1
    assert admins[0].password_hash == original_hash
    assert verify_password(admins[0].password_hash, "senha-nova-que-nao-deve-substituir") is False
