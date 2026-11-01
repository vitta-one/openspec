"""Regressions for the read-only Administrator QA reception panel."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.admin_preview.reception_service import load_reception_preview
from vitta_one.admin_preview.service import LocalAdminPreviewDisabledError
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models import (  # noqa: F401 - register models for SQLite fixtures
    AuthSession, Consultation, Patient, Professional,
    ProfessionalAvailabilitySlot, QueueEntry, User,
)


@pytest.fixture(autouse=True)
def qa_settings(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "true")
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


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
    engine.dispose()


def token_for(db, role=Role.ADMINISTRADOR):
    user = User(
        email=f"{role.value.casefold()}@qa.test",
        password_hash="fixture-not-plain-text",
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def patient(db, name, cpf):
    obj = Patient(name=name, cpf=cpf)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def queue(db, who, status, priority, *, entered, finished=None, withdrawn=None):
    obj = QueueEntry(
        patient_id=who.id, consultation_id=None,
        symptoms="INFORMAÇÃO CLÍNICA RESTRITA AO BANCO",
        priority=priority, status=status,
        entered_at=entered, finished_at=finished, withdrawn_at=withdrawn,
    )
    db.add(obj)
    db.commit()
    return obj


def appointment(db, who, doctor, instant, status="AGENDADA"):
    slot = ProfessionalAvailabilitySlot(
        professional_id=doctor.id, starts_at=instant, status="BOOKED",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    item = Consultation(
        patient_id=who.id, professional_id=doctor.id,
        availability_slot_id=slot.id, scheduled_at=instant, status=status,
    )
    db.add(item)
    db.commit()
    return item


def load(db, token, **filters):
    return load_reception_preview(
        db, token=token, start_day="2026-10-14", end_day="2026-10-14",
        now=datetime(2026, 10, 14, 15, tzinfo=timezone.utc), **filters,
    )


def test_empty_data_stays_empty_with_valid_timestamp(db):
    snapshot = load(db, token_for(db))
    assert snapshot.waiting_count == snapshot.attending_count == 0
    assert snapshot.finalized_count == snapshot.withdrawn_count == 0
    assert snapshot.active_rows == snapshot.history_rows == snapshot.consultation_rows == []
    assert snapshot.updated_at.startswith("14/10/2026")


def test_queue_order_history_period_and_privacy(db):
    auth = token_for(db)
    a = patient(db, "Paciente amarelo", "00000000001")
    b = patient(db, "Paciente vermelho", "00000000002")
    c = patient(db, "Paciente atendido", "00000000003")
    old = datetime(2026, 10, 14, 8, tzinfo=timezone.utc)
    newer = datetime(2026, 10, 14, 10, tzinfo=timezone.utc)

    queue(db, a, "AGUARDANDO", "AMARELO", entered=old)
    queue(db, b, "AGUARDANDO", "VERMELHO", entered=newer)
    queue(db, c, "EM_ATENDIMENTO", "VERDE", entered=old)
    queue(
        db, a, "FINALIZADO", "VERDE", entered=old,
        finished=datetime(2026, 10, 14, 12, tzinfo=timezone.utc),
    )
    queue(
        db, b, "RETIRADO", "VERMELHO", entered=old,
        withdrawn=datetime(2026, 10, 14, 5, tzinfo=timezone.utc),
    )
    queue(
        db, c, "FINALIZADO", "VERDE", entered=old,
        finished=datetime(2026, 10, 14, 2, tzinfo=timezone.utc),  # local day 13
    )

    result = load(db, auth)
    assert (result.waiting_count, result.attending_count) == (2, 1)
    assert (result.finalized_count, result.withdrawn_count) == (1, 1)
    assert [r["patient_name"] for r in result.active_rows] == [
        "Paciente vermelho", "Paciente amarelo", "Paciente atendido",
    ]
    assert {r["status"] for r in result.history_rows} == {"FINALIZADO", "RETIRADO"}
    assert all("UTC" not in r["event_at"] for r in result.history_rows)
    assert all("14/10/2026" in r["event_at"] for r in result.history_rows)
    assert "INFORMAÇÃO CLÍNICA" not in str(result)
    assert "cpf" not in str(result).casefold()

    red = load(db, auth, priority_filter="VERMELHO")
    assert red.waiting_count == 1
    assert red.finalized_count == 0 and red.withdrawn_count == 1
    assert all(row["priority"] == "VERMELHO" for row in red.active_rows + red.history_rows)
    retired = load(db, auth, status_filter="RETIRADO")
    assert retired.active_rows == []
    assert [row["status"] for row in retired.history_rows] == ["RETIRADO"]
    assert retired.finalized_count == 1  # KPI counts remain status-wide


def test_agenda_queries_real_consultations_and_professional_filter(db):
    auth = token_for(db)
    who = patient(db, "Paciente particular", "00000000004")
    doctor1 = Professional(name="Dra. Um", registration_identifier="QA-1")
    doctor2 = Professional(name="Dr. Dois", registration_identifier="QA-2")
    db.add(doctor1)
    db.add(doctor2)
    db.commit()
    db.refresh(doctor1)
    db.refresh(doctor2)
    appointment(db, who, doctor1, datetime(2026, 10, 14, 12, tzinfo=timezone.utc))
    appointment(
        db, who, doctor2, datetime(2026, 10, 14, 14, tzinfo=timezone.utc),
        status="CANCELADA",
    )
    appointment(db, who, doctor1, datetime(2026, 10, 15, 12, tzinfo=timezone.utc))

    result = load(db, auth)
    assert result.consultation_total == 2
    assert [row["status_label"] for row in result.consultation_rows] == ["Agendada", "Cancelada"]
    assert "Paciente particular" not in str(result.consultation_rows)
    assert result.consultation_rows[0]["scheduled_at"] == "14/10/2026 às 09:00"
    filtered = load(db, auth, professional_filter=str(doctor1.id))
    assert filtered.consultation_total == 1
    assert [row["professional_name"] for row in filtered.consultation_rows] == ["Dra. Um"]
    assert [(row["label"], row["value"]) for row in result.professional_options] == [
        ("Dr. Dois", str(doctor2.id)), ("Dra. Um", str(doctor1.id)),
    ]


def test_preview_revalidates_role_session_flag_before_any_read(db, monkeypatch):
    admin = token_for(db)
    receptionist = token_for(db, Role.RECEPCIONISTA)

    with pytest.raises(RoleForbiddenError):
        load(db, receptionist)
    with pytest.raises(AuthenticationRequiredError):
        load(db, "")
    monkeypatch.setenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "false")
    with pytest.raises(LocalAdminPreviewDisabledError):
        load(db, admin)


@pytest.mark.parametrize("overrides", [
    {"start_day": "2026-10-15", "end_day": "2026-10-14"},
    {"start_day": "2026-10-14", "end_day": "2026-11-15"},
    {"start_day": "INVALID"},
    {"priority_filter": "AZUL"},
    {"status_filter": "INVENTADO"},
    {"professional_filter": "999"},
])
def test_bad_filters_fail_without_returning_data(db, overrides):
    auth = token_for(db)
    arguments = dict(
        token=auth, start_day="2026-10-14", end_day="2026-10-14",
    )
    arguments.update(overrides)
    with pytest.raises(ValueError):
        load_reception_preview(db, **arguments)


def test_preview_reads_without_mutating_queue_records(db):
    auth = token_for(db)
    who = patient(db, "Paciente estável", "00000000006")
    queue(
        db, who, "AGUARDANDO", "VERDE",
        entered=datetime(2026, 10, 14, 14, tzinfo=timezone.utc),
    )
    load(db, auth)
    entry = db.exec(select(QueueEntry)).one()
    assert entry.status == "AGUARDANDO"
    assert entry.priority == "VERDE"
