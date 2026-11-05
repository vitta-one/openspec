"""Reception patient directory: SQL pagination, search, RBAC and privacy."""

from datetime import timedelta

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.patient_queue.application import reception_list_patient_directory


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _token(db: Session, role: Role) -> str:
    user = User(
        email=f"directory-{role.value.lower()}@example.invalid",
        password_hash="unused",
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _patient(db: Session, index: int, *, name: str = "Paciente", phone: str | None = None):
    patient = Patient(
        name=f"{name} {index:02d}",
        cpf=f"{index + 1:011d}",
        phone=phone,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_directory_returns_only_persisted_identity_and_no_cpf(db):
    token = _token(db, Role.RECEPCIONISTA)
    first = _patient(db, 0, name="Ana", phone="11987654321")
    _patient(db, 1, name="Bruna")

    rows, total = reception_list_patient_directory(db, token=token)
    assert total == 2
    assert [row["id"] for row in rows] == [first.id, first.id + 1]
    assert set(rows[0]) == {"id", "name", "phone", "href"}
    assert rows[0]["href"] == f"/recepcao/pacientes/{first.id}"
    assert rows[0]["phone"] == "11987654321"
    assert rows[1]["phone"] == ""
    assert all("cpf" not in row and "symptoms" not in row for row in rows)


def test_directory_uses_stable_sql_pagination_and_real_counts(db):
    token = _token(db, Role.RECEPCIONISTA)
    for index in range(23):
        _patient(db, index)

    first, total = reception_list_patient_directory(db, token=token, page=1)
    second, second_total = reception_list_patient_directory(db, token=token, page=2)
    third, third_total = reception_list_patient_directory(db, token=token, page=3)
    assert (total, second_total, third_total) == (23, 23, 23)
    assert (len(first), len(second), len(third)) == (10, 10, 3)
    assert len({row["id"] for row in first + second + third}) == 23
    assert [r["name"] for r in first] == sorted(r["name"] for r in first)

    empty, empty_total = reception_list_patient_directory(db, token=token, page=10)
    assert empty == [] and empty_total == 23


def test_directory_finds_name_cpf_and_normalized_phone(db):
    token = _token(db, Role.RECEPCIONISTA)
    person = _patient(db, 29, name="Helena Castro", phone="11984521102")
    _patient(db, 30, name="Outro nome", phone="1132221111")

    for search in ("helena", "000.000.000-30", "(11) 98452-1102", "845211"):
        rows, total = reception_list_patient_directory(db, token=token, search=search)
        assert total == 1
        assert rows[0]["id"] == person.id


def test_directory_treats_like_wildcards_as_text(db):
    token = _token(db, Role.RECEPCIONISTA)
    _patient(db, 1, name="Ana")
    _patient(db, 2, name="Beatriz")

    for term in ("%", "_", "\\"):
        rows, total = reception_list_patient_directory(db, token=token, search=term)
        assert rows == []
        assert total == 0


def test_directory_revalidates_session_and_role_on_each_read(db):
    receptionist = _token(db, Role.RECEPCIONISTA)
    doctor = _token(db, Role.MEDICO)
    _patient(db, 0)

    assert reception_list_patient_directory(db, token=receptionist)[1] == 1
    with pytest.raises(AuthenticationRequiredError):
        reception_list_patient_directory(db, token="")
    with pytest.raises(RoleForbiddenError):
        reception_list_patient_directory(db, token=doctor)
    with pytest.raises(RoleForbiddenError):
        reception_list_patient_directory(db, token=doctor, search="Paciente")


def test_directory_empty_and_filtered_empty_are_distinct(db):
    token = _token(db, Role.RECEPCIONISTA)
    assert reception_list_patient_directory(db, token=token) == ([], 0)
    _patient(db, 0, name="Teresa")
    assert reception_list_patient_directory(db, token=token, search="Inexistente") == ([], 0)
