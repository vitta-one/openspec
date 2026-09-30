"""Authorization tests for the explicit local Administrator QA preview."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.admin_preview.service import (
    LocalAdminPreviewDisabledError,
    require_local_admin_preview,
)
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User


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


def test_preview_is_disabled_by_default(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", raising=False)
    token = _token_for(db, Role.ADMINISTRADOR, "admin-preview-off@example.com")

    with pytest.raises(LocalAdminPreviewDisabledError):
        require_local_admin_preview(db, token)


def test_admin_is_allowed_only_when_preview_is_explicitly_enabled(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token_for(db, Role.ADMINISTRADOR, "admin-preview@example.com")

    identity = require_local_admin_preview(db, token)

    assert identity.role is Role.ADMINISTRADOR
    assert identity.email == "admin-preview@example.com"


@pytest.mark.parametrize(
    "role",
    [Role.RECEPCIONISTA, Role.MEDICO, Role.FINANCEIRO],
)
def test_preview_does_not_widen_non_admin_permissions(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    role: Role,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token_for(db, role, f"{role.value.casefold()}-preview@example.com")

    with pytest.raises(RoleForbiddenError):
        require_local_admin_preview(db, token)


def test_preview_rejects_missing_session(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")

    with pytest.raises(AuthenticationRequiredError):
        require_local_admin_preview(db, "")
