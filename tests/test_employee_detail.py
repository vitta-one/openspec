"""Consulta da ficha administrativa: RBAC, dados persistidos e contas legadas."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session, revoke_session
from vitta_one.auth.staff_service import get_employee_detail
from vitta_one.models.auth import AuthSession, User
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(
        engine,
        tables=[
            User.__table__, AuthSession.__table__, Professional.__table__,
            Specialty.__table__, ProfessionalSpecialty.__table__,
        ],
    )
    with Session(engine) as session:
        yield session
    engine.dispose()


def _user(db, role: Role, email: str, name: str | None = None) -> User:
    user = User(
        email=email, display_name=name,
        password_hash=hash_password("SenhaDeTeste123!"), role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token(db, user: User) -> str:
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_employee_detail_uses_persisted_name_and_never_returns_password(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    person = _user(db, Role.RECEPCIONISTA, "recepcao@example.test", "Ana Souza")
    detail = get_employee_detail(db, token=_token(db, admin), employee_id=person.id)
    assert detail["name"] == "Ana Souza"
    assert detail["has_name"] is True
    assert detail["email"] == "recepcao@example.test"
    assert detail["role_label"] == "Recepcionista"
    assert detail["professional_identifier"] == ""
    assert "password_hash" not in detail
    assert "must_change_password" not in detail


def test_employee_detail_handles_legacy_name_without_using_email_as_name(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    legacy = _user(db, Role.RECEPCIONISTA, "legacy@example.test")
    detail = get_employee_detail(db, token=_token(db, admin), employee_id=legacy.id)
    assert detail["name"] == "Nome não informado"
    assert detail["has_name"] is False
    assert detail["email"] == legacy.email


def test_doctor_detail_reuses_existing_professional_and_specialty(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    doctor = _user(db, Role.MEDICO, "medico@example.test")
    professional = Professional(
        name="Marina Lopes", user_id=doctor.id,
        registration_identifier="IDENT-0123", is_active=True,
    )
    specialty = Specialty(name="Pediatria", normalized_name="pediatria")
    db.add(professional)
    db.add(specialty)
    db.commit()
    db.refresh(professional)
    db.refresh(specialty)
    db.add(ProfessionalSpecialty(
        professional_id=professional.id, specialty_id=specialty.id,
    ))
    db.commit()

    detail = get_employee_detail(db, token=_token(db, admin), employee_id=doctor.id)
    assert detail["name"] == "Marina Lopes"
    assert detail["has_name"] is True
    assert detail["professional_identifier"] == "IDENT-0123"
    assert detail["professional_status"] == "Ativo"
    assert detail["specialties"] == "Pediatria"


def test_detail_for_medical_user_without_professional_is_not_fabricated(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    doctor = _user(db, Role.MEDICO, "medico@example.test", "Lia Lima")
    detail = get_employee_detail(db, token=_token(db, admin), employee_id=doctor.id)
    assert detail["professional_identifier"] == ""
    assert detail["specialties"] == ""
    assert detail["name"] == "Lia Lima"


def test_not_found_and_non_staff_account_are_not_exposed(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    patient = _user(db, Role.PACIENTE, "paciente@example.test", "Paciente")
    token = _token(db, admin)
    assert get_employee_detail(db, token=token, employee_id=987654) is None
    assert get_employee_detail(db, token=token, employee_id=patient.id) is None
    assert get_employee_detail(db, token=token, employee_id=admin.id) is None


@pytest.mark.parametrize("role", [Role.RECEPCIONISTA, Role.MEDICO, Role.FINANCEIRO, Role.PACIENTE])
def test_other_roles_cannot_read_employee_detail(db, role):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    user = _user(db, role, f"{role.value.lower()}@example.test")
    with pytest.raises(RoleForbiddenError):
        get_employee_detail(db, token=_token(db, user), employee_id=admin.id)


def test_revoked_or_missing_session_cannot_read_employee_detail(db):
    admin = _user(db, Role.ADMINISTRADOR, "admin@example.test")
    person = _user(db, Role.RECEPCIONISTA, "recepcao@example.test")
    token = _token(db, admin)
    assert revoke_session(db, token)
    for invalid in (token, ""):
        with pytest.raises(AuthenticationRequiredError):
            get_employee_detail(db, token=invalid, employee_id=person.id)
