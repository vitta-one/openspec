"""Regressions for specialty editor, state transitions and RBAC."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.models.professional import ProfessionalSpecialty, Specialty
from vitta_one.professional_directory.application import (
    admin_get_specialty,
    admin_rename_specialty,
    admin_set_specialty_active,
)
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryValidationError,
    create_professional,
    create_specialty,
    get_specialty,
    rename_specialty,
    set_specialty_active,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_edit_and_status_keep_identity_and_medical_links(db):
    area = create_specialty(db, name="Cardiologia")
    doctor = create_professional(
        db, name="Dra. Ana", registration_identifier="QA-ANA",
        specialty_ids=[area.id],
    )
    original_id = area.id
    edited = rename_specialty(
        db, specialty_id=area.id, name=" Cardiologia Clínica ",
        expected_name="Cardiologia",
    )
    assert edited.id == original_id
    assert get_specialty(db, specialty_id=original_id).name == "Cardiologia Clínica"
    set_specialty_active(
        db, specialty_id=original_id, is_active=False, expected_active=True
    )
    assert db.get(Specialty, original_id).is_active is False
    set_specialty_active(
        db, specialty_id=original_id, is_active=True, expected_active=False
    )
    assert db.get(Specialty, original_id).is_active is True
    links = db.exec(
        select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == doctor.id
        )
    ).all()
    assert len(links) == 1
    assert links[0].specialty_id == original_id
    assert len(db.exec(select(Specialty)).all()) == 1


def test_blank_duplicate_and_stale_rename_preserve_existing_data(db):
    first = create_specialty(db, name="Clínica Geral")
    second = create_specialty(db, name="Dermatologia")
    with pytest.raises(DirectoryValidationError):
        rename_specialty(db, specialty_id=first.id, name="   ")
    with pytest.raises(DirectoryValidationError):
        rename_specialty(db, specialty_id=first.id, name="a" * 121)
    with pytest.raises(DirectoryConflictError):
        rename_specialty(db, specialty_id=second.id, name=" CLÍNICA   GERAL ")
    with pytest.raises(DirectoryConflictError, match="Reabra a edição"):
        rename_specialty(
            db, specialty_id=first.id, name="Outra",
            expected_name="Nome antigo",
        )
    assert db.get(Specialty, first.id).name == "Clínica Geral"
    assert db.get(Specialty, second.id).name == "Dermatologia"


def test_stale_status_update_does_not_reverse_a_newer_change(db):
    area = create_specialty(db, name="Neurologia")
    set_specialty_active(db, specialty_id=area.id, is_active=False,
                         expected_active=True)
    with pytest.raises(DirectoryConflictError, match="Atualize a lista"):
        set_specialty_active(db, specialty_id=area.id, is_active=False,
                             expected_active=True)
    assert db.get(Specialty, area.id).is_active is False


def test_equivalent_rename_keeps_same_record(db):
    area = create_specialty(db, name="Ortopedia")
    current = rename_specialty(
        db, specialty_id=area.id, name="  Ortopedia  ",
        expected_name="Ortopedia",
    )
    assert current.id == area.id
    assert len(db.exec(select(Specialty)).all()) == 1


@pytest.mark.parametrize("role", [Role.RECEPCIONISTA, Role.MEDICO, Role.FINANCEIRO])
def test_non_admin_cannot_read_or_mutate_specialty(db, role):
    area = create_specialty(db, name="Pediatria")
    user = User(
        email=f"{role.value.lower()}-specialty@qa.invalid",
        password_hash="qa-hash", role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user_id=user.id, ttl=timedelta(hours=1))
    with pytest.raises(RoleForbiddenError):
        admin_get_specialty(db, token=token, specialty_id=area.id)
    with pytest.raises(RoleForbiddenError):
        admin_rename_specialty(
            db, token=token, specialty_id=area.id, name="Nova"
        )
    with pytest.raises(RoleForbiddenError):
        admin_set_specialty_active(
            db, token=token, specialty_id=area.id, is_active=False
        )
    assert db.get(Specialty, area.id).is_active is True


def test_admin_get_reads_latest_persisted_name(db):
    area = create_specialty(db, name="Oftalmologia")
    user = User(email="admin-specialty@qa.invalid",
                password_hash="qa-hash", role=Role.ADMINISTRADOR.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_session(db, user_id=user.id, ttl=timedelta(hours=1))
    rename_specialty(db, specialty_id=area.id, name="Oftalmologia Clínica")
    fresh = admin_get_specialty(db, token=token, specialty_id=area.id)
    assert fresh.name == "Oftalmologia Clínica"
    assert fresh.id == area.id
