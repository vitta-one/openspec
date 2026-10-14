"""Regression tests for bounded admin directory summaries and their access control."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.professional_directory.application import (
    admin_list_recent_professionals,
    admin_list_recent_specialties,
)
from vitta_one.professional_directory.service import (
    create_professional,
    create_specialty,
    list_professionals,
    list_specialties,
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


def _token(db: Session, role: Role, email: str) -> str:
    user = User(email=email, password_hash="not-a-real-password", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_specialty_dashboard_limits_to_three_newest_and_breaks_ties_by_id(db):
    items = [create_specialty(db, name=f"Area {n}") for n in range(5)]
    timestamp = datetime(2026, 10, 10, tzinfo=timezone.utc)
    # All timestamps equal to exercise deterministic primary-key tie breaking.
    for item in items:
        item.created_at = timestamp
        db.add(item)
    db.commit()
    admin = _token(db, Role.ADMINISTRADOR, "admin@qa.invalid")
    recent = admin_list_recent_specialties(db, token=admin)
    assert [row.id for row in recent] == [items[4].id, items[3].id, items[2].id]
    assert len(list_specialties(db)) == 5


def test_professional_dashboard_limits_to_three_newest_and_preserves_full_list(db):
    specialty = create_specialty(db, name="Clinica QA")
    doctors = [
        create_professional(
            db, name=f"Medico {n}", registration_identifier=f"QA-{n}",
            specialty_ids=[specialty.id],
        )
        for n in range(5)
    ]
    # Latest by date takes precedence over ID.
    for i, doctor in enumerate(doctors):
        doctor.created_at = datetime(2026, 10, 1 + i, tzinfo=timezone.utc)
        db.add(doctor)
    db.commit()
    admin = _token(db, Role.ADMINISTRADOR, "admin-doc@qa.invalid")
    recent = admin_list_recent_professionals(db, token=admin)
    assert [row.id for row in recent] == [doctors[4].id, doctors[3].id, doctors[2].id]
    assert len(list_professionals(db)) == 5


@pytest.mark.parametrize("role", [Role.RECEPCIONISTA, Role.MEDICO, Role.FINANCEIRO])
def test_non_admin_cannot_read_bounded_dashboard_lists(db, role):
    token = _token(db, role, f"{role.value.lower()}@qa.invalid")
    with pytest.raises(RoleForbiddenError):
        admin_list_recent_specialties(db, token=token)
    with pytest.raises(RoleForbiddenError):
        admin_list_recent_professionals(db, token=token)


def test_anonymous_cannot_read_bounded_dashboard_lists(db):
    with pytest.raises(AuthenticationRequiredError):
        admin_list_recent_specialties(db, token="")
    with pytest.raises(AuthenticationRequiredError):
        admin_list_recent_professionals(db, token="")


@pytest.mark.parametrize("bad_limit", [0, -1, 101])
def test_invalid_summary_limits_are_rejected(db, bad_limit):
    with pytest.raises(ValueError):
        list_specialties(db, recent_limit=bad_limit)
    with pytest.raises(ValueError):
        list_professionals(db, recent_limit=bad_limit)
