"""Database-backed reception dashboard metrics and RBAC regression tests."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.auth.state import _ROLE_BY_ROUTE
from vitta_one.models import (  # noqa: F401 - register all database tables
    AuthSession, Consultation, Patient, Professional,
    ProfessionalAvailabilitySlot, QueueEntry, User,
)
from vitta_one.reception.dashboard.application import reception_overview
from vitta_one.reception.dashboard.service import get_reception_overview


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def auth(db, role, email):
    user = User(email=email, password_hash="unused", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def consultation(db, when, *, status="AGENDADA", label="Paciente QA"):
    patient = Patient(name=label, cpf=f"{len(db.exec(__import__('sqlmodel').select(Patient)).all()) + 1:011d}")
    professional = Professional(
        name="Dra. Consulta QA", registration_identifier=f"INT-{len(db.exec(__import__('sqlmodel').select(Professional)).all())+1}"
    )
    db.add(patient)
    db.add(professional)
    db.commit()
    db.refresh(patient)
    db.refresh(professional)
    slot = ProfessionalAvailabilitySlot(
        professional_id=professional.id, starts_at=when,
        status="BOOKED",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    item = Consultation(
        patient_id=patient.id, professional_id=professional.id,
        availability_slot_id=slot.id, scheduled_at=when, status=status,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item, patient


def queue(db, patient, *, status, priority="VERDE", entered=None, finished=None):
    item = QueueEntry(
        patient_id=patient.id, consultation_id=None,
        symptoms="Sintoma de fixture somente no banco", priority=priority,
        status=status, entered_at=entered or datetime(2026, 10, 14, tzinfo=timezone.utc),
        finished_at=finished,
    )
    db.add(item)
    db.commit()
    return item


def test_empty_overview_reports_honest_zero_and_no_upcoming(db):
    snap = get_reception_overview(db, now=datetime(2026, 10, 14, 15, tzinfo=timezone.utc))
    assert snap.clinic_date == "2026-10-14"
    assert snap.scheduled_today == 0
    assert snap.waiting == snap.attending == snap.finished_today == 0
    assert snap.confirmed_today == snap.arrivals_pending == 0
    assert not snap.next_consultations


def test_real_counts_are_disjoint_and_next_consultations_exclude_cancelled(db):
    now = datetime(2026, 10, 14, 15, tzinfo=timezone.utc)  # Noon at the clinic
    future, patient = consultation(db, datetime(2026, 10, 14, 17, tzinfo=timezone.utc))
    past, _ = consultation(db, datetime(2026, 10, 14, 13, tzinfo=timezone.utc))
    confirmed, _ = consultation(db, datetime(2026, 10, 14, 18, tzinfo=timezone.utc), status="CONFIRMADA")
    cancelled, _ = consultation(db, datetime(2026, 10, 14, 19, tzinfo=timezone.utc), status="CANCELADA")
    queue(db, patient, status="AGUARDANDO", priority="VERMELHO")
    queue(db, patient, status="AGUARDANDO", priority="AMARELO")
    queue(db, patient, status="EM_ATENDIMENTO")
    queue(db, patient, status="FINALIZADO", finished=datetime(2026, 10, 14, 14, tzinfo=timezone.utc))
    queue(db, patient, status="FINALIZADO", finished=datetime(2026, 10, 13, 14, tzinfo=timezone.utc))
    snap = get_reception_overview(db, now=now)
    assert snap.scheduled_today == 3
    assert snap.arrivals_pending == 1
    assert snap.confirmed_today == 1
    assert snap.waiting == 2 and snap.attending == 1 and snap.finished_today == 1
    assert (snap.waiting_red, snap.waiting_yellow, snap.waiting_green) == (1, 1, 0)
    assert [c.id for c in snap.next_consultations] == [future.id]
    assert cancelled.id not in [c.id for c in snap.next_consultations]
    assert past.id not in [c.id for c in snap.next_consultations]
    assert "Sintoma" not in repr(snap)


def test_day_is_clinic_local_not_utc_and_future_is_limited(db):
    now = datetime(2026, 10, 15, 2, 0, tzinfo=timezone.utc)  # 14 Oct 23h in SP
    consultation(db, datetime(2026, 10, 15, 1, 0, tzinfo=timezone.utc))
    consultation(db, datetime(2026, 10, 15, 4, 0, tzinfo=timezone.utc))
    snap = get_reception_overview(db, now=now)
    assert snap.clinic_date == "2026-10-14"
    assert snap.scheduled_today == 1
    assert len(snap.next_consultations) == 1


def test_dashboard_application_requires_exact_reception_role(db):
    receptionist = auth(db, Role.RECEPCIONISTA, "reception-dash@example.invalid")
    doctor = auth(db, Role.MEDICO, "doctor-dash@example.invalid")
    admin = auth(db, Role.ADMINISTRADOR, "admin-dash@example.invalid")
    assert reception_overview(db, token=receptionist).scheduled_today == 0
    with pytest.raises(AuthenticationRequiredError):
        reception_overview(db, token="")
    with pytest.raises(RoleForbiddenError):
        reception_overview(db, token=doctor)
    with pytest.raises(RoleForbiddenError):
        reception_overview(db, token=admin)


def test_every_reception_route_is_guarded_by_server_role():
    for route in ("/recepcao", "/recepcao/agenda", "/recepcao/pacientes", "/recepcao/fila"):
        assert _ROLE_BY_ROUTE[route] is Role.RECEPCIONISTA
