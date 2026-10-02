"""Authorization boundaries for clinical record access."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.admin_preview.service import LocalAdminPreviewDisabledError
from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.clinical_care.application import (
    admin_preview_patient_history,
    doctor_save_active_record,
)
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
    user = User(
        email=email,
        password_hash=hash_password("unit-test-pass"),
        role=role.value,
    )
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


@pytest.mark.parametrize(
    "role",
    [Role.ADMINISTRADOR, Role.RECEPCIONISTA, Role.FINANCEIRO],
)
def test_non_doctor_roles_cannot_save_clinical_content_before_lookup(
    db: Session,
    role: Role,
) -> None:
    user = _user(db, role, f"{role.value.casefold()}-clinical@example.com")
    token = _token(db, user)
    with pytest.raises(RoleForbiddenError):
        doctor_save_active_record(
            db,
            token=token,
            entry_id=999999,
            chief_complaint="Não deve ser lido",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
        )


def test_missing_and_expired_doctor_sessions_are_rejected(db: Session) -> None:
    with pytest.raises(AuthenticationRequiredError):
        doctor_save_active_record(
            db,
            token="",
            entry_id=999999,
            chief_complaint="Não deve ser lido",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
        )

    doctor = _user(db, Role.MEDICO, "expired-clinical@example.com")
    expired = _token(
        db,
        doctor,
        now=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(AuthenticationRequiredError):
        doctor_save_active_record(
            db,
            token=expired,
            entry_id=999999,
            chief_complaint="Não deve ser lido",
            anamnesis="",
            diagnosis="",
            conduct_notes="",
        )


def test_admin_has_no_general_clinical_history_api_when_qa_is_disabled(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false")
    admin = _user(db, Role.ADMINISTRADOR, "admin-no-qa@example.com")
    token = _token(db, admin)
    with pytest.raises(LocalAdminPreviewDisabledError):
        admin_preview_patient_history(
            db,
            token=token,
            patient_id=999999,
            page=1,
        )


def test_admin_qa_history_requires_admin_role(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    finance = _user(db, Role.FINANCEIRO, "finance-clinical@example.com")
    token = _token(db, finance)
    with pytest.raises(RoleForbiddenError):
        admin_preview_patient_history(
            db,
            token=token,
            patient_id=999999,
            page=1,
        )
