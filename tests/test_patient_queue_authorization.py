"""Authorization tests for patient queue application operations."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.patient_queue.application import (
    doctor_claim_next,
    reception_create_patient,
    reception_enqueue,
    reception_list_queue,
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


def _session_for_role(db: Session, role: Role) -> str:
    user = User(
        email=f"{role.value.casefold()}@exemplo.com",
        password_hash=hash_password("senha-teste"),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_reception_operations_require_reception_role(db: Session) -> None:
    reception_token = _session_for_role(db, Role.RECEPCIONISTA)
    doctor_token = _session_for_role(db, Role.MEDICO)

    patient = reception_create_patient(
        db,
        token=reception_token,
        name="Paciente Autorizado",
        cpf="52998224725",
    )
    reception_enqueue(
        db,
        token=reception_token,
        patient_id=patient.id,
        symptoms="Dor",
        priority="VERDE",
    )
    assert len(reception_list_queue(db, token=reception_token)) == 1

    with pytest.raises(RoleForbiddenError):
        reception_create_patient(
            db,
            token=doctor_token,
            name="Não permitido",
            cpf="16899535009",
        )
    with pytest.raises(RoleForbiddenError):
        reception_list_queue(db, token=doctor_token)


def test_doctor_operations_reject_reception_role_before_mutation(db: Session) -> None:
    reception_token = _session_for_role(db, Role.RECEPCIONISTA)
    patient = reception_create_patient(
        db,
        token=reception_token,
        name="Paciente Fila",
        cpf="52998224725",
    )
    reception_enqueue(
        db,
        token=reception_token,
        patient_id=patient.id,
        symptoms="Dor",
        priority="VERMELHO",
    )

    with pytest.raises(RoleForbiddenError):
        doctor_claim_next(db, token=reception_token)

    assert len(reception_list_queue(db, token=reception_token)) == 1


def test_missing_and_expired_sessions_cannot_read_or_mutate_queue(db: Session) -> None:
    with pytest.raises(AuthenticationRequiredError):
        reception_list_queue(db, token="")

    expired_user = User(
        email="expired-reception@example.invalid",
        password_hash=hash_password("senha-teste"),
        role=Role.RECEPCIONISTA.value,
    )
    db.add(expired_user)
    db.commit()
    db.refresh(expired_user)
    expired_token = create_session(
        db,
        user_id=expired_user.id,
        ttl=timedelta(minutes=1),
        now=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(AuthenticationRequiredError):
        reception_create_patient(
            db,
            token=expired_token,
            name="Não deve persistir",
            cpf="16899535009",
        )

    with pytest.raises(AuthenticationRequiredError):
        reception_list_queue(db, token=expired_token)
