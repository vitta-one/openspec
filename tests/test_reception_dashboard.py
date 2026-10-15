"""Database-backed reception dashboard metrics and RBAC regression tests."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event
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


def test_empty_overview_reports_honest_zero_and_empty_calendar(db):
    snap = get_reception_overview(db, now=datetime(2026, 10, 14, 15, tzinfo=timezone.utc))
    assert snap.clinic_date == "2026-10-14"
    assert snap.scheduled_today == 0
    assert snap.waiting == snap.attending == snap.finished_today == 0
    assert snap.confirmed_today == snap.arrivals_pending == 0
    assert not snap.calendar_consultations


def test_real_counts_are_disjoint_and_calendar_keeps_operational_statuses(db):
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
    assert [c.id for c in snap.calendar_consultations] == [
        past.id,
        future.id,
        confirmed.id,
        cancelled.id,
    ]
    assert snap.calendar_consultations[-1].status.value == "CANCELADA"
    assert "Sintoma" not in repr(snap)


def test_calendar_dates_are_clinic_local_not_utc(db):
    now = datetime(2026, 10, 15, 2, 0, tzinfo=timezone.utc)  # 14 Oct 23h in SP
    local_late_evening, _ = consultation(
        db, datetime(2026, 10, 15, 1, 0, tzinfo=timezone.utc)
    )
    local_next_day, _ = consultation(
        db, datetime(2026, 10, 15, 4, 0, tzinfo=timezone.utc)
    )
    snap = get_reception_overview(db, now=now)
    assert snap.clinic_date == "2026-10-14"
    assert snap.scheduled_today == 1
    assert {item.id for item in snap.calendar_consultations} == {
        local_late_evening.id,
        local_next_day.id,
    }


def test_calendar_covers_seven_clinic_local_dates_and_keeps_cancelled(db):
    now = datetime(2026, 10, 14, 15, tzinfo=timezone.utc)
    before, _ = consultation(
        db, datetime(2026, 10, 14, 2, 59, 59, tzinfo=timezone.utc)
    )
    first, _ = consultation(
        db, datetime(2026, 10, 14, 3, 0, tzinfo=timezone.utc)
    )
    last, _ = consultation(
        db,
        datetime(2026, 10, 21, 2, 59, 59, tzinfo=timezone.utc),
        status="CANCELADA",
    )
    after, _ = consultation(
        db, datetime(2026, 10, 21, 3, 0, tzinfo=timezone.utc)
    )

    snapshot = get_reception_overview(db, now=now)

    assert [item.id for item in snapshot.calendar_consultations] == [
        first.id,
        last.id,
    ]
    assert snapshot.calendar_consultations[-1].status.value == "CANCELADA"
    assert before.id not in {item.id for item in snapshot.calendar_consultations}
    assert after.id not in {item.id for item in snapshot.calendar_consultations}


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


def test_pending_arrivals_are_bounded_and_only_show_overdue_unconfirmed_today(db):
    now = datetime(2026, 10, 14, 15, tzinfo=timezone.utc)
    overdue = [
        consultation(
            db,
            now - timedelta(minutes=minute),
            label=f"Paciente pendente {minute}",
        )[0]
        for minute in range(7, 0, -1)
    ]
    consultation(
        db,
        now - timedelta(minutes=8),
        status="CONFIRMADA",
        label="Paciente já confirmado",
    )
    consultation(
        db,
        now - timedelta(minutes=9),
        status="CANCELADA",
        label="Paciente cancelado",
    )

    snapshot = get_reception_overview(db, now=now)

    assert snapshot.arrivals_pending == 7
    assert len(snapshot.pending_arrivals) == 5
    assert [item.id for item in snapshot.pending_arrivals] == [
        item.id for item in overdue[:5]
    ]
    assert [item.scheduled_at for item in snapshot.pending_arrivals] == sorted(
        item.scheduled_at for item in snapshot.pending_arrivals
    )
    assert all(
        item.patient_name not in {"Paciente já confirmado", "Paciente cancelado"}
        for item in snapshot.pending_arrivals
    )
    assert "Sintoma" not in repr(snapshot.pending_arrivals)


def test_overview_uses_four_projection_queries(db):
    statements = []
    engine = db.get_bind()

    def record_query(_conn, _cursor, statement, _parameters, _context, _executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", record_query)
    try:
        get_reception_overview(
            db, now=datetime(2026, 10, 14, 15, tzinfo=timezone.utc)
        )
    finally:
        event.remove(engine, "before_cursor_execute", record_query)

    assert len(statements) == 4
