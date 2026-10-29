"""Validações do comando local `make user` sem tocar no PostgreSQL persistente."""

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.local_qa import LocalQaAccountError
from vitta_one.auth.local_user_cli import create_local_user, require_isolated_local_database
from vitta_one.auth.roles import Role
from vitta_one.auth.security import verify_password
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional


@pytest.fixture(autouse=True)
def local_qa_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://vittaqa:test-secret@127.0.0.1:5433/vitta_one_qa",
    )
    monkeypatch.setenv("POSTGRES_USER", "vittaqa")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test-secret")
    monkeypatch.setenv("POSTGRES_DB", "vitta_one_qa")
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    monkeypatch.delenv("VITTA_ONE_QA_DISPOSABLE_DATABASE", raising=False)


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(
        engine, tables=[User.__table__, Patient.__table__, Professional.__table__]
    )
    with Session(engine) as session:
        yield session


@pytest.mark.parametrize(
    "role", (Role.ADMINISTRADOR, Role.RECEPCIONISTA, Role.FINANCEIRO)
)
def test_creates_local_role_without_printing_or_persisting_plain_password(
    db: Session, role: Role
) -> None:
    password = "SenhaDeTeste123!"
    account = create_local_user(
        db,
        email=f"  {role.value}@EXEMPLO.COM  ",
        password=password,
        role=role,
    )
    assert account.email == f"{role.value.lower()}@exemplo.com"
    assert account.role == role.value
    assert account.password_hash != password
    assert verify_password(account.password_hash, password)
    assert account.must_change_password is False


def test_duplicate_email_is_rejected_without_overwriting_password(db: Session) -> None:
    first = create_local_user(
        db, email="qa@exemplo.com", password="PrimeiraSenha123", role=Role.RECEPCIONISTA
    )
    original_hash = first.password_hash

    with pytest.raises(LocalQaAccountError, match="Já existe"):
        create_local_user(
            db,
            email="  QA@EXEMPLO.COM ",
            password="SegundaSenha123",
            role=Role.ADMINISTRADOR,
        )
    stored = db.exec(select(User).where(User.email == "qa@exemplo.com")).one()
    assert stored.password_hash == original_hash
    assert stored.role == Role.RECEPCIONISTA.value


@pytest.mark.parametrize("email,password", [
    ("sem-arroba", "SenhaValida123!"),
    ("teste@dominio", "SenhaValida123!"),
    ("teste@exemplo.com", "curta"),
])
def test_invalid_login_is_rejected(db: Session, email: str, password: str) -> None:
    with pytest.raises(LocalQaAccountError):
        create_local_user(db, email=email, password=password, role=Role.FINANCEIRO)
    assert db.exec(select(User)).all() == []


@pytest.mark.parametrize("variable,value", [
    ("DATABASE_URL", "postgresql+psycopg://vittaqa:test-secret@servidor:5433/vitta_one_qa"),
    ("DATABASE_URL", "postgresql+psycopg://vittaqa:test-secret@127.0.0.1:5432/vitta_one_qa"),
    ("POSTGRES_PASSWORD", "senha-diferente"),
    ("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false"),
    ("VITTA_ONE_QA_DISPOSABLE_DATABASE", "yes"),
])
def test_non_qa_environment_is_rejected(
    monkeypatch: pytest.MonkeyPatch, db: Session, variable: str, value: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(LocalQaAccountError, match="Criação recusada"):
        require_isolated_local_database()
    with pytest.raises(LocalQaAccountError):
        create_local_user(
            db, email="bloqueado@exemplo.com", password="SenhaValida123!",
            role=Role.ADMINISTRADOR,
        )
    assert db.exec(select(User)).all() == []


def test_medical_account_requires_and_links_an_available_professional(db: Session) -> None:
    professional = Professional(name="Médico QA", registration_identifier="QA-MED-001")
    db.add(professional)
    db.commit()
    db.refresh(professional)

    with pytest.raises(LocalQaAccountError, match="ID"):
        create_local_user(
            db, email="sem-vinculo@exemplo.com", password="SenhaValida123!",
            role=Role.MEDICO,
        )

    user = create_local_user(
        db, email="medico@exemplo.com", password="SenhaValida123!",
        role=Role.MEDICO, linked_id=professional.id,
    )
    db.refresh(professional)
    assert professional.user_id == user.id

    with pytest.raises(LocalQaAccountError, match="vinculado"):
        create_local_user(
            db, email="outro@exemplo.com", password="SenhaValida123!",
            role=Role.MEDICO, linked_id=professional.id,
        )


def test_patient_account_requires_explicit_consent_and_links_patient(db: Session) -> None:
    patient = Patient(name="Paciente QA", cpf="12345678909")
    db.add(patient)
    db.commit()
    db.refresh(patient)

    with pytest.raises(LocalQaAccountError, match="consentimento"):
        create_local_user(
            db, email="paciente@exemplo.com", password="SenhaValida123!",
            role=Role.PACIENTE, linked_id=patient.id,
        )
    assert db.exec(select(User)).all() == []

    user = create_local_user(
        db, email="paciente@exemplo.com", password="SenhaValida123!",
        role=Role.PACIENTE, linked_id=patient.id, patient_consent_confirmed=True,
    )
    db.refresh(patient)
    assert patient.user_id == user.id


def test_unlinked_roles_reject_clinical_ids(db: Session) -> None:
    with pytest.raises(LocalQaAccountError, match="não aceita vínculo"):
        create_local_user(
            db, email="financeiro@exemplo.com", password="SenhaValida123!",
            role=Role.FINANCEIRO, linked_id=3,
        )
