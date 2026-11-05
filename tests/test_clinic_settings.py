"""Clinic configuration: persistence, RBAC, validation, and audit invariants."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.clinic_settings.service import (
    ClinicSettingsConflictError,
    ClinicSettingsValidationError,
    get_clinic_location,
    save_clinic_location,
)
from vitta_one.models.auth import User
from vitta_one.models.clinic_settings import ClinicConfiguration, ClinicConfigurationChange


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _token(db: Session, role: Role, email: str) -> str:
    user = User(email=email, role=role.value, password_hash=hash_password("test-secret"))
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_fallback_only_until_persisted_and_restart(db, monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_NAME", "Clínica do Ambiente")
    monkeypatch.setenv("VITTA_ONE_CLINIC_ADDRESS", "Rua do Ambiente, 1")
    before = get_clinic_location(db)
    assert (before.name, before.persisted, before.revision) == ("Clínica do Ambiente", False, 0)
    admin = _token(db, Role.ADMINISTRADOR, "admin@clinic.test")
    saved = save_clinic_location(
        db, token=admin, name="  Clínica   Persistida  ",
        address="  Rua Teste, 100  ", expected_revision=0,
    )
    assert (saved.name, saved.address, saved.persisted, saved.revision) == (
        "Clínica Persistida", "Rua Teste, 100", True, 1,
    )
    monkeypatch.setenv("VITTA_ONE_CLINIC_NAME", "Valor antigo")
    with Session(db.bind) as another_session:
        persisted = get_clinic_location(another_session)
    assert (persisted.name, persisted.address, persisted.revision) == (
        "Clínica Persistida", "Rua Teste, 100", 1,
    )


@pytest.mark.parametrize("role", [
    Role.RECEPCIONISTA, Role.MEDICO, Role.PACIENTE, Role.FINANCEIRO,
])
def test_non_administrators_cannot_write(db, role):
    token = _token(db, role, f"{role.value.lower()}@clinic.test")
    with pytest.raises(RoleForbiddenError):
        save_clinic_location(db, token=token, name="Clínica", address="Rua 1", expected_revision=0)
    assert db.exec(select(ClinicConfiguration)).all() == []


def test_missing_session_cannot_write(db):
    with pytest.raises(AuthenticationRequiredError):
        save_clinic_location(db, token="invalid", name="Clínica", address="Rua 1", expected_revision=0)


@pytest.mark.parametrize(("field", "name", "address"), [
    ("name", "", "Rua 1"),
    ("name", "  \t  ", "Rua 1"),
    ("name", "a" * 161, "Rua 1"),
    ("address", "Clínica", ""),
    ("address", "Clínica", "  \n  "),
    ("address", "Clínica", "x" * 501),
])
def test_invalid_fields_rejected(db, field, name, address):
    token = _token(db, Role.ADMINISTRADOR, f"admin-{field}-{len(name)}-{len(address)}@clinic.test")
    with pytest.raises(ClinicSettingsValidationError) as exc:
        save_clinic_location(db, token=token, name=name, address=address, expected_revision=0)
    assert exc.value.field == field
    assert db.exec(select(ClinicConfiguration)).all() == []


def test_update_is_atomic_audited_idempotent_and_revision_protected(db):
    admin = _token(db, Role.ADMINISTRADOR, "admin@clinic.test")
    first = save_clinic_location(
        db, token=admin, name="Clínica A", address="Rua A", expected_revision=0,
    )
    repeat = save_clinic_location(
        db, token=admin, name="Clínica A", address="Rua A", expected_revision=1,
    )
    assert repeat.revision == first.revision
    updated = save_clinic_location(
        db, token=admin, name="Clínica B", address="Rua B", expected_revision=1,
    )
    assert updated.revision == 2
    with pytest.raises(ClinicSettingsConflictError):
        save_clinic_location(
            db, token=admin, name="Clínica Antiga", address="Rua Antiga", expected_revision=1,
        )
    rows = db.exec(select(ClinicConfiguration)).all()
    audit = db.exec(select(ClinicConfigurationChange).order_by(ClinicConfigurationChange.id)).all()
    assert len(rows) == 1
    assert rows[0].name == "Clínica B"
    assert len(audit) == 2
    assert audit[0].previous_name is None
    assert (audit[1].previous_name, audit[1].name) == ("Clínica A", "Clínica B")
