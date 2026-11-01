"""Regression tests for the restricted, read-only admin QA patient dossier."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.admin_preview.service import (
    LocalAdminPreviewDisabledError,
    get_preview_patient_detail,
    get_preview_patient_identity,
)
from vitta_one.admin_preview.state import _serialize_patient_operation
from vitta_one.appointment_scheduling.temporal import format_clinic_datetime
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.auth.state import _ADMIN_PREVIEW_ROUTES, _ROLE_BY_ROUTE
from vitta_one.models import Patient, QueueEntry, User


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


def _token(db: Session, role: Role, suffix: str) -> str:
    user = User(
        email=f"qa-detail-{suffix}@example.com",
        password_hash=hash_password("senha-de-testes"),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _patients_with_queue(db: Session) -> tuple[Patient, Patient, datetime]:
    ana = Patient(name="Ana QA", cpf="12345678901")
    bruno = Patient(name="Bruno QA", cpf="98765432100")
    db.add(ana)
    db.add(bruno)
    db.commit()
    db.refresh(ana)
    db.refresh(bruno)
    entered_at = datetime(2026, 10, 31, 15, 30, tzinfo=timezone.utc)
    db.add(
        QueueEntry(
            patient_id=ana.id,
            symptoms="Teste operacional Ana",
            priority="VERDE",
            status="FINALIZADO",
            entered_at=entered_at,
        )
    )
    db.add(
        QueueEntry(
            patient_id=bruno.id,
            symptoms="Teste operacional Bruno",
            priority="AMARELO",
            status="RETIRADO",
            entered_at=entered_at,
        )
    )
    db.commit()
    return ana, bruno, entered_at


def test_detail_scopes_queue_entries_by_patient_and_does_not_load_clinical_data(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token(db, Role.ADMINISTRADOR, "admin")
    ana, bruno, entered_at = _patients_with_queue(db)

    patient, entries = get_preview_patient_detail(db, token=token, patient_id=ana.id)
    assert patient.id == ana.id
    assert len(entries) == 1
    assert entries[0].patient_id == ana.id
    assert entries[0].symptoms == "Teste operacional Ana"
    assert all(entry.patient_id != bruno.id for entry in entries)

    payload = _serialize_patient_operation(entries[0])
    assert payload["entered_at"] == format_clinic_datetime(entered_at)
    assert "UTC" not in payload["entered_at"]
    assert set(payload) == {
        "id", "entered_at", "symptoms", "priority", "priority_label",
        "status", "status_label",
    }


def test_nonexistent_and_invalid_patient_do_not_return_another_patient(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token(db, Role.ADMINISTRADOR, "missing")
    ana, _, _ = _patients_with_queue(db)

    assert get_preview_patient_identity(db, token=token, patient_id=-1) is None
    assert get_preview_patient_detail(db, token=token, patient_id=999999) == (None, [])
    assert get_preview_patient_detail(db, token=token, patient_id=0) == (None, [])
    patient, entries = get_preview_patient_detail(db, token=token, patient_id=ana.id)
    assert patient.id == ana.id and len(entries) == 1


@pytest.mark.parametrize("role", [Role.RECEPCIONISTA, Role.MEDICO, Role.PACIENTE, Role.FINANCEIRO])
def test_detail_denies_other_roles_before_reading(
    db: Session, monkeypatch: pytest.MonkeyPatch, role: Role
) -> None:
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token(db, role, role.value.casefold())
    ana, _, _ = _patients_with_queue(db)

    with pytest.raises(RoleForbiddenError):
        get_preview_patient_detail(db, token=token, patient_id=ana.id)


def test_detail_denies_when_qa_disabled_and_when_session_missing(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = _token(db, Role.ADMINISTRADOR, "disabled")
    ana, _, _ = _patients_with_queue(db)
    monkeypatch.delenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", raising=False)

    with pytest.raises(LocalAdminPreviewDisabledError):
        get_preview_patient_detail(db, token=token, patient_id=ana.id)

    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    with pytest.raises(AuthenticationRequiredError):
        get_preview_patient_detail(db, token="", patient_id=ana.id)


def test_patient_detail_route_remains_local_qa_only() -> None:
    assert "/admin/pacientes" in _ADMIN_PREVIEW_ROUTES
    assert "/admin/pacientes/[patient_id]" in _ADMIN_PREVIEW_ROUTES
    assert "/admin/pacientes/[patient_id]" not in _ROLE_BY_ROUTE
