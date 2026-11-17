"""Authorized, privacy-minimal dashboard aggregates for Admin and Reception."""
from datetime import datetime, timedelta, timezone
import importlib

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models import (  # noqa: F401 - register every table for metadata
    AuthSession,
    Consultation,
    EmailNotification,
    Patient,
    Professional,
    ProfessionalAvailabilitySlot,
    Specialty,
    User,
)

def test_dashboard_projection_contracts_are_available():
    admin = importlib.util.find_spec("vitta_one.admin_dashboard")
    reception = importlib.import_module("vitta_one.reception.dashboard.application")

    assert admin is not None
    assert hasattr(reception, "reception_email_metrics")


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


def _token(db: Session, role: Role, email: str) -> str:
    user = User(email=email, password_hash="unused", role=role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_session(db, user_id=user.id, ttl=timedelta(hours=1))


def _consultation(db: Session, scheduled_at: datetime, *, status="AGENDADA"):
    patient = Patient(
        name="Paciente sintético",
        cpf=f"{len(db.exec(select(Patient)).all()) + 1:011d}",
    )
    professional = Professional(
        name="Profissional sintético",
        registration_identifier=f"INT-{len(db.exec(select(Professional)).all()) + 1}",
        is_active=False,
    )
    db.add_all((patient, professional))
    db.commit()
    db.refresh(patient)
    db.refresh(professional)
    slot = ProfessionalAvailabilitySlot(
        professional_id=professional.id, starts_at=scheduled_at, status="BOOKED"
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    consultation = Consultation(
        patient_id=patient.id,
        professional_id=professional.id,
        availability_slot_id=slot.id,
        scheduled_at=scheduled_at,
        status=status,
    )
    db.add(consultation)
    db.commit()


def test_admin_dashboard_uses_real_counts_and_clinic_local_day(db):
    from vitta_one.admin_dashboard.application import admin_dashboard_snapshot

    admin = _token(db, Role.ADMINISTRADOR, "admin-dashboard@example.invalid")
    db.add_all(
        (
            User(email="doctor-dashboard@example.invalid", password_hash="unused", role="MEDICO"),
            User(email="reception-dashboard@example.invalid", password_hash="unused", role="RECEPCIONISTA"),
            User(email="patient-dashboard@example.invalid", password_hash="unused", role="PACIENTE"),
        )
    )
    db.add_all(
        (
            Professional(name="Ativo", registration_identifier="INT-A", is_active=True),
            Professional(name="Inativo", registration_identifier="INT-I", is_active=False),
            Specialty(name="Ativa", normalized_name="ativa", is_active=True),
            Specialty(name="Inativa", normalized_name="inativa", is_active=False),
        )
    )
    db.commit()

    _consultation(db, datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc))
    _consultation(db, datetime(2026, 11, 16, 2, 59, 59, tzinfo=timezone.utc))
    _consultation(db, datetime(2026, 11, 17, 3, 0, tzinfo=timezone.utc))
    _consultation(db, datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc), status="CANCELADA")

    snapshot = admin_dashboard_snapshot(
        db, token=admin, now=datetime(2026, 11, 16, 15, tzinfo=timezone.utc)
    )

    assert snapshot.active_professionals == 1
    assert snapshot.active_specialties == 1
    assert snapshot.consultations_today == 1
    assert snapshot.staff_accounts == 2


def test_admin_dashboard_denies_non_administrators(db):
    from vitta_one.admin_dashboard.application import admin_dashboard_snapshot

    receptionist = _token(db, Role.RECEPCIONISTA, "reception-dashboard-deny@example.invalid")

    with pytest.raises(RoleForbiddenError):
        admin_dashboard_snapshot(db, token=receptionist)


def test_admin_dashboard_reports_zero_for_empty_clinic(db):
    from vitta_one.admin_dashboard.application import admin_dashboard_snapshot

    admin = _token(db, Role.ADMINISTRADOR, "admin-dashboard-empty@example.invalid")
    snapshot = admin_dashboard_snapshot(
        db, token=admin, now=datetime(2026, 11, 16, 15, tzinfo=timezone.utc)
    )

    assert (
        snapshot.active_professionals,
        snapshot.active_specialties,
        snapshot.consultations_today,
        snapshot.staff_accounts,
    ) == (0, 0, 0, 0)


def test_reception_email_metrics_group_provider_states_and_local_date_window(db):
    from vitta_one.reception.dashboard.application import reception_email_metrics

    token = _token(db, Role.RECEPCIONISTA, "reception-email-metrics@example.invalid")
    statuses = (
        "ACCEPTED", "DELIVERED", "FAILED", "PENDING", "SENDING", "UNKNOWN",
        "NOT_CONFIGURED", "SUPPRESSED",
    )
    for index, status in enumerate(statuses):
        db.add(
            EmailNotification(
                kind="booking_confirmed",
                event_key=f"event-{index}",
                recipient_hash=f"{index:064x}",
                entity_id=1,
                status=status,
                created_at=datetime(2026, 10, 18, 3, 0, tzinfo=timezone.utc),
            )
        )
    db.add(
        EmailNotification(
            kind="booking_cancelled",
            event_key="outside-window",
            recipient_hash="f" * 64,
            entity_id=1,
            status="FAILED",
            created_at=datetime(2026, 10, 18, 2, 59, 59, tzinfo=timezone.utc),
        )
    )
    db.add(
        EmailNotification(
            kind="payment_received",
            event_key="financial-message",
            recipient_hash="e" * 64,
            entity_id=1,
            status="FAILED",
            created_at=datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc),
        )
    )
    db.commit()

    metrics = reception_email_metrics(
        db, token=token, now=datetime(2026, 11, 16, 15, tzinfo=timezone.utc)
    )

    assert (metrics.accepted, metrics.delivered, metrics.failed, metrics.pending) == (1, 1, 1, 4)
    assert "@" not in repr(metrics)


def test_reception_email_metrics_denies_other_roles(db):
    from vitta_one.reception.dashboard.application import reception_email_metrics

    doctor = _token(db, Role.MEDICO, "doctor-email-metrics@example.invalid")

    with pytest.raises(RoleForbiddenError):
        reception_email_metrics(db, token=doctor)


def test_reception_email_metrics_reports_zero_when_outbox_is_empty(db):
    from vitta_one.reception.dashboard.application import reception_email_metrics

    token = _token(db, Role.RECEPCIONISTA, "reception-email-empty@example.invalid")
    metrics = reception_email_metrics(
        db, token=token, now=datetime(2026, 11, 16, 15, tzinfo=timezone.utc)
    )

    assert (metrics.accepted, metrics.delivered, metrics.failed, metrics.pending) == (0, 0, 0, 0)
