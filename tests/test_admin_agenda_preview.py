"""QA agenda read model: authorization, privacy, month filtering and real dates."""

from collections import Counter
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.admin_preview.agenda_state import build_preview_calendar_days
from vitta_one.admin_preview.service import (
    LocalAdminPreviewDisabledError,
    admin_agenda_snapshot,
)
from vitta_one.appointment_scheduling.service import (
    create_availability_slot,
    schedule_consultation,
)
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.patient_queue.service import create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def clinic_tz(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


def _token(db, role, email):
    user = User(email=email, password_hash=hash_password("senha-teste"), role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def test_calendar_indicates_only_persisted_days_and_keeps_empty_dates_selectable():
    days = build_preview_calendar_days(
        "2026-10", "2026-10-31", "2026-10-31",
        Counter({"2026-10-30": 2}),
        Counter({"2026-10-31": 1}),
    )
    selected = next(day for day in days if day["date_label"] == "2026-10-31")
    available = next(day for day in days if day["date_label"] == "2026-10-30")
    assert selected["is_today"] and selected["is_selected"]
    assert selected["consultation_count"] == 1 and not selected["has_slots"]
    assert available["slot_count"] == 2 and available["has_slots"]


def test_agenda_preview_denies_disabled_and_non_admin(db, monkeypatch):
    admin = _token(db, Role.ADMINISTRADOR, "qa-agenda@example.com")
    monkeypatch.delenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", raising=False)
    with pytest.raises(LocalAdminPreviewDisabledError):
        admin_agenda_snapshot(db, token=admin, start_date="2026-10-01", end_date="2026-10-31")

    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    reception = _token(db, Role.RECEPCIONISTA, "qa-reception@example.com")
    with pytest.raises(RoleForbiddenError):
        admin_agenda_snapshot(db, token=reception, start_date="2026-10-01", end_date="2026-10-31")
    with pytest.raises(AuthenticationRequiredError):
        admin_agenda_snapshot(db, token="", start_date="2026-10-01", end_date="2026-10-31")


def test_agenda_preview_filters_db_and_never_serializes_patient(db, monkeypatch):
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    token = _token(db, Role.ADMINISTRADOR, "admin-agenda@example.com")
    specialty = create_specialty(db, name="Clínica geral agenda")
    first = create_professional(db, name="Dra. A", registration_identifier="REG-QA-A", specialty_ids=[specialty.id])
    second = create_professional(db, name="Dr. B", registration_identifier="REG-QA-B", specialty_ids=[specialty.id])
    patient = create_patient(db, name="PACIENTE SENSÍVEL", cpf="52998224725")
    now = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)
    slot_a = create_availability_slot(db, professional_id=first.id, starts_at=datetime(2026, 10, 30, 12, tzinfo=timezone.utc), now=now)
    create_availability_slot(db, professional_id=second.id, starts_at=datetime(2026, 10, 30, 13, tzinfo=timezone.utc), now=now)
    create_availability_slot(db, professional_id=first.id, starts_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc), now=now)
    schedule_consultation(db, patient_id=patient.id, slot_id=slot_a.id, now=now)

    snapshot = admin_agenda_snapshot(
        db, token=token, start_date="2026-10-01", end_date="2026-10-31",
        professional_id=first.id,
    )
    assert len(snapshot.slots) == 1
    assert len(snapshot.consultations) == 1
    assert snapshot.consultations[0].professional_name == "Dra. A"
    assert "patient_name" not in snapshot.consultations[0].__dataclass_fields__
    assert "patient_id" not in snapshot.consultations[0].__dataclass_fields__
    assert len(snapshot.professionals) == 2

    with pytest.raises(ValueError):
        admin_agenda_snapshot(db, token=token, start_date="2026-10-01", end_date="2026-10-31", professional_id=999999)
