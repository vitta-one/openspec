"""Tests for professional and specialty directory business rules."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.roles import Role
from vitta_one.models.auth import User
from vitta_one.models.professional import ProfessionalSpecialty
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryValidationError,
    create_professional,
    create_specialty,
    list_available_medical_accounts,
    list_professionals,
    list_specialties,
    normalize_registration_identifier,
    normalize_specialty_key,
    rename_specialty,
    set_professional_active,
    set_specialty_active,
    update_professional,
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


def _user(db: Session, role: Role, email: str) -> User:
    user = User(email=email, password_hash="test-hash", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_normalization_is_generic_and_stable() -> None:
    assert normalize_specialty_key("  Cirurgia   Geral  ") == "cirurgia geral"
    assert normalize_specialty_key("CARDIOLOGIA") == "cardiologia"
    assert normalize_registration_identifier("  crm-sp   123  ") == "CRM-SP 123"


def test_specialty_create_rename_uniqueness_and_activation(db: Session) -> None:
    cardiology = create_specialty(db, name=" Cardiologia ")
    assert cardiology.name == "Cardiologia"
    assert cardiology.normalized_name == "cardiologia"
    assert cardiology.is_active is True

    with pytest.raises(DirectoryConflictError):
        create_specialty(db, name="  CARDIOLOGIA  ")

    neurology = create_specialty(db, name="Neurologia")
    with pytest.raises(DirectoryConflictError):
        rename_specialty(db, specialty_id=neurology.id, name="cardiologia")

    renamed = rename_specialty(db, specialty_id=neurology.id, name="Neuro Clínica")
    assert renamed.name == "Neuro Clínica"
    assert renamed.normalized_name == "neuro clínica"

    inactive = set_specialty_active(db, specialty_id=cardiology.id, is_active=False)
    assert inactive.is_active is False
    active = set_specialty_active(db, specialty_id=cardiology.id, is_active=True)
    assert active.is_active is True

    assert [item.name for item in list_specialties(db)] == [
        "Cardiologia",
        "Neuro Clínica",
    ]


def test_professional_specialty_optional_and_deduplicates_associations(db: Session) -> None:
    cardiology = create_specialty(db, name="Cardiologia")
    pediatrics = create_specialty(db, name="Pediatria")

    without_specialty = create_professional(
        db,
        name="Dra. Sem Especialidade",
        registration_identifier="REG-0",
        specialty_ids=[],
    )
    initial = next(item for item in list_professionals(db) if item.id == without_specialty.id)
    assert initial.specialties == ()

    professional = create_professional(
        db,
        name=" Dra. Ana   Silva ",
        registration_identifier=" reg-1 ",
        specialty_ids=[cardiology.id, pediatrics.id, cardiology.id],
    )
    assert professional.name == "Dra. Ana Silva"
    assert professional.registration_identifier == "REG-1"

    rows = db.exec(
        __import__("sqlmodel").select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == professional.id
        )
    ).all()
    assert {row.specialty_id for row in rows} == {cardiology.id, pediatrics.id}
    assert len(rows) == 2


def test_edit_can_remove_all_specialties_without_changing_identity(db: Session) -> None:
    specialty = create_specialty(db, name="Clínica Geral")
    doctor = _user(db, Role.MEDICO, "linked@example.invalid")
    professional = create_professional(
        db, name="Dra. Editável", registration_identifier="REG-S",
        specialty_ids=[specialty.id], user_id=doctor.id,
    )
    updated = update_professional(
        db, professional_id=professional.id, name="Dra. Editada",
        registration_identifier="REG-S", specialty_ids=[], user_id=doctor.id,
    )
    assert updated.user_id == doctor.id
    item = next(row for row in list_professionals(db) if row.id == professional.id)
    assert item.name == "Dra. Editada"
    assert item.specialties == ()


def test_professional_status_confirmation_rejects_stale_state(db: Session) -> None:
    specialty = create_specialty(db, name="Cardiologia")
    professional = create_professional(
        db, name="Dr. Situação", registration_identifier="REG-STATUS",
        specialty_ids=[specialty.id],
    )
    disabled = set_professional_active(
        db, professional_id=professional.id, is_active=False, expected_active=True,
    )
    assert disabled.is_active is False
    with pytest.raises(DirectoryConflictError, match="situação"):
        set_professional_active(
            db, professional_id=professional.id, is_active=False, expected_active=True,
        )
    assert next(
        item for item in list_professionals(db) if item.id == professional.id
    ).is_active is False


def test_professionals_can_share_specialties_but_registration_is_unique(db: Session) -> None:
    specialty = create_specialty(db, name="Clínica Geral")
    first = create_professional(
        db,
        name="Dr. Um",
        registration_identifier="REG-10",
        specialty_ids=[specialty.id],
    )
    second = create_professional(
        db,
        name="Dr. Dois",
        registration_identifier="REG-11",
        specialty_ids=[specialty.id],
    )
    assert first.id != second.id

    with pytest.raises(DirectoryConflictError):
        create_professional(
            db,
            name="Dr. Duplicado",
            registration_identifier=" reg-10 ",
            specialty_ids=[specialty.id],
        )


def test_inactive_specialty_cannot_be_added_but_historical_link_is_preserved(
    db: Session,
) -> None:
    historical = create_specialty(db, name="Especialidade Histórica")
    active = create_specialty(db, name="Especialidade Ativa")
    professional = create_professional(
        db,
        name="Dra. Histórico",
        registration_identifier="REG-H",
        specialty_ids=[historical.id],
    )
    set_specialty_active(db, specialty_id=historical.id, is_active=False)

    updated = update_professional(
        db,
        professional_id=professional.id,
        name="Dra. Histórico Atualizada",
        registration_identifier="REG-H",
        specialty_ids=[historical.id, active.id],
    )
    assert updated.name == "Dra. Histórico Atualizada"

    other = create_professional(
        db,
        name="Dr. Outro",
        registration_identifier="REG-O",
        specialty_ids=[active.id],
    )
    with pytest.raises(DirectoryValidationError):
        update_professional(
            db,
            professional_id=other.id,
            name="Dr. Outro",
            registration_identifier="REG-O",
            specialty_ids=[active.id, historical.id],
        )

    item = next(item for item in list_professionals(db) if item.id == professional.id)
    assert {specialty.name for specialty in item.specialties} == {
        "Especialidade Histórica",
        "Especialidade Ativa",
    }
    assert any(not specialty.is_active for specialty in item.specialties)


def test_medical_user_link_is_optional_role_checked_and_unique(db: Session) -> None:
    specialty = create_specialty(db, name="Cardiologia")
    doctor = _user(db, Role.MEDICO, "medico1@example.com")
    other_doctor = _user(db, Role.MEDICO, "medico2@example.com")
    receptionist = _user(db, Role.RECEPCIONISTA, "recepcao@example.com")

    without_user = create_professional(
        db,
        name="Dr. Sem Login",
        registration_identifier="REG-A",
        specialty_ids=[specialty.id],
    )
    assert without_user.user_id is None

    with pytest.raises(DirectoryValidationError):
        create_professional(
            db,
            name="Dr. Role Errada",
            registration_identifier="REG-B",
            specialty_ids=[specialty.id],
            user_id=receptionist.id,
        )

    linked = create_professional(
        db,
        name="Dr. Com Login",
        registration_identifier="REG-C",
        specialty_ids=[specialty.id],
        user_id=doctor.id,
    )
    assert linked.user_id == doctor.id

    with pytest.raises(DirectoryConflictError):
        create_professional(
            db,
            name="Dr. Conta Repetida",
            registration_identifier="REG-D",
            specialty_ids=[specialty.id],
            user_id=doctor.id,
        )

    options = list_available_medical_accounts(db)
    assert [(option.id, option.email) for option in options] == [
        (other_doctor.id, other_doctor.email)
    ]
    assert not hasattr(options[0], "password_hash")


def test_professional_activation_preserves_links_and_user(db: Session) -> None:
    specialty = create_specialty(db, name="Ortopedia")
    doctor = _user(db, Role.MEDICO, "ortopedista@example.com")
    professional = create_professional(
        db,
        name="Dr. Ortopedista",
        registration_identifier="REG-ORT",
        specialty_ids=[specialty.id],
        user_id=doctor.id,
    )

    set_professional_active(db, professional_id=professional.id, is_active=False)
    inactive_item = list_professionals(db)[0]
    assert inactive_item.is_active is False
    assert inactive_item.user_id == doctor.id
    assert [item.id for item in inactive_item.specialties] == [specialty.id]

    set_professional_active(db, professional_id=professional.id, is_active=True)
    active_item = list_professionals(db)[0]
    assert active_item.is_active is True
    assert active_item.user_id == doctor.id
    assert [item.id for item in active_item.specialties] == [specialty.id]


def test_update_replaces_specialties_atomically_after_validation(db: Session) -> None:
    first = create_specialty(db, name="Primeira")
    second = create_specialty(db, name="Segunda")
    inactive = create_specialty(db, name="Inativa")
    set_specialty_active(db, specialty_id=inactive.id, is_active=False)

    professional = create_professional(
        db,
        name="Dra. Transação",
        registration_identifier="REG-T",
        specialty_ids=[first.id],
    )

    with pytest.raises(DirectoryValidationError):
        update_professional(
            db,
            professional_id=professional.id,
            name="Nome não deve persistir",
            registration_identifier="REG-T2",
            specialty_ids=[second.id, inactive.id],
        )

    item = list_professionals(db)[0]
    assert item.name == "Dra. Transação"
    assert item.registration_identifier == "REG-T"
    assert [specialty.id for specialty in item.specialties] == [first.id]


def test_edit_professional_can_remove_all_specialty_links(db: Session) -> None:
    specialty = create_specialty(db, name="Clínica geral")
    doctor = create_professional(
        db,
        name="Dra. Disponível",
        registration_identifier="REG-SEM-VINCULO",
        specialty_ids=[specialty.id],
    )

    updated = update_professional(
        db,
        professional_id=doctor.id,
        name="Dra. Disponível",
        registration_identifier="REG-SEM-VINCULO",
        specialty_ids=[],
    )

    assert updated.id == doctor.id
    item = next(row for row in list_professionals(db) if row.id == doctor.id)
    assert item.specialties == ()
    links = db.exec(
        __import__("sqlmodel").select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == doctor.id
        )
    ).all()
    assert links == []


def test_professional_can_remove_all_specialties_and_reject_invalid_ids(db: Session) -> None:
    specialty = create_specialty(db, name="Cardiologia")
    professional = create_professional(
        db, name="Dr. Atualização", registration_identifier="REG-NEW",
        specialty_ids=[specialty.id],
    )
    update_professional(
        db, professional_id=professional.id, name="Dr. Atualização",
        registration_identifier="REG-NEW", specialty_ids=[],
    )
    assert next(
        item for item in list_professionals(db) if item.id == professional.id
    ).specialties == ()

    with pytest.raises(DirectoryValidationError, match="inválida"):
        update_professional(
            db, professional_id=professional.id, name="Dr. Atualização",
            registration_identifier="REG-NEW", specialty_ids=["não-numérico"],
        )
    with pytest.raises(DirectoryValidationError, match="não existe"):
        update_professional(
            db, professional_id=professional.id, name="Dr. Atualização",
            registration_identifier="REG-NEW", specialty_ids=[987654],
        )
