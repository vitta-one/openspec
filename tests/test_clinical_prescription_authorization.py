"""Authorization boundaries for clinical prescription operations."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.admin_preview.service import LocalAdminPreviewDisabledError
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.clinical_prescription.application import (
    admin_preview_prescriptions_for_records,
    doctor_create_prescription,
    doctor_get_printable_prescription,
    doctor_list_current_prescriptions,
)
from vitta_one.models.auth import User
from vitta_one.ui.prescription_components import NO_DIGITAL_SIGNATURE_NOTICE


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
def test_non_doctor_roles_are_rejected_before_prescription_lookup(
    db: Session,
    role: Role,
) -> None:
    user = _user(db, role, f"{role.value.casefold()}-prescription@example.com")
    token = _token(db, user)

    with pytest.raises(RoleForbiddenError):
        doctor_list_current_prescriptions(
            db,
            token=token,
            clinical_care_record_id=999999,
        )
    with pytest.raises(RoleForbiddenError):
        doctor_create_prescription(
            db,
            token=token,
            clinical_care_record_id=999999,
            medication_or_item="Não deve ser lido",
            instructions="Não deve ser lido",
        )
    with pytest.raises(RoleForbiddenError):
        doctor_get_printable_prescription(
            db,
            token=token,
            prescription_id=999999,
        )


def test_missing_and_expired_sessions_are_rejected_before_prescription_lookup(
    db: Session,
) -> None:
    with pytest.raises(AuthenticationRequiredError):
        doctor_create_prescription(
            db,
            token="",
            clinical_care_record_id=999999,
            medication_or_item="Não deve ser lido",
            instructions="Não deve ser lido",
        )

    doctor = _user(db, Role.MEDICO, "expired-prescription@example.com")
    expired = _token(
        db,
        doctor,
        now=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    with pytest.raises(AuthenticationRequiredError):
        doctor_get_printable_prescription(
            db,
            token=expired,
            prescription_id=999999,
        )


def test_print_contract_exposes_explicit_unsigned_notice() -> None:
    assert NO_DIGITAL_SIGNATURE_NOTICE == "Documento sem assinatura digital."


def test_print_requires_session_before_lookup(db: Session) -> None:
    with pytest.raises(AuthenticationRequiredError):
        doctor_get_printable_prescription(
            db,
            token="",
            prescription_id=999999,
        )


def test_admin_has_no_general_prescription_api_when_qa_disabled(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false")
    admin = _user(db, Role.ADMINISTRADOR, "admin-prescription-no-qa@example.com")
    token = _token(db, admin)
    with pytest.raises(LocalAdminPreviewDisabledError):
        admin_preview_prescriptions_for_records(
            db,
            token=token,
            clinical_care_record_ids=[999999],
        )


@pytest.mark.parametrize("role", [Role.MEDICO, Role.RECEPCIONISTA, Role.FINANCEIRO])
def test_admin_qa_prescription_projection_requires_admin_role(
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    role: Role,
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    user = _user(db, role, f"qa-{role.value.casefold()}-prescription@example.com")
    token = _token(db, user)
    with pytest.raises(RoleForbiddenError):
        admin_preview_prescriptions_for_records(
            db,
            token=token,
            clinical_care_record_ids=[999999],
        )

