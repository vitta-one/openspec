"""Safe medical onboarding without actual email or production data."""

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.authorization import PasswordChangeRequiredError, require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, verify_password
from vitta_one.auth.service import (
    TemporaryPasswordError,
    authenticate_user,
    complete_temporary_password_change,
    create_session,
)
from vitta_one.models.auth import User
from vitta_one.models.professional import Professional, ProfessionalSpecialty
from vitta_one.professional_directory.email_sender import send_medical_welcome
from vitta_one.professional_directory.service import (
    DirectoryConflictError,
    DirectoryValidationError,
    register_medical_professional,
    create_specialty,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _specialty(db):
    return create_specialty(db, name="Medicina Geral QA")


def test_atomic_medical_registration_generates_safe_internal_identifier(db):
    specialty = _specialty(db)
    result = register_medical_professional(
        db, name="  Dra.   Ana  ", email="  ANA@EXAMPLE.INVALID ",
        specialty_ids=[specialty.id, specialty.id],
    )
    assert result.name == "Dra. Ana"
    assert result.email == "ana@example.invalid"
    assert result.temporary_password and len(result.temporary_password) >= 32
    identity = db.get(User, result.user_id)
    professional = db.get(Professional, result.professional_id)
    assert identity.role == Role.MEDICO.value
    assert identity.must_change_password is True
    assert identity.temporary_password_expires_at is not None
    assert identity.password_hash != result.temporary_password
    assert verify_password(identity.password_hash, result.temporary_password)
    assert professional.user_id == identity.id
    assert professional.registration_identifier.startswith("INT-")
    assert professional.onboarding_email_status == "PENDING"
    assert len(db.exec(
        select(ProfessionalSpecialty).where(
            ProfessionalSpecialty.professional_id == professional.id
        )
    ).all()) == 1


def test_same_email_second_create_does_not_duplicate_user_or_professional(db):
    specialty = _specialty(db)
    register_medical_professional(
        db, name="Primeira", email="doctor@example.invalid",
        specialty_ids=[specialty.id],
    )
    with pytest.raises(DirectoryConflictError):
        register_medical_professional(
            db, name="Segunda", email="DOCTOR@example.invalid",
            specialty_ids=[specialty.id],
        )
    assert len(db.exec(select(User)).all()) == 1
    assert len(db.exec(select(Professional)).all()) == 1


def test_existing_unlinked_doctor_is_reused_without_password_change(db):
    specialty = _specialty(db)
    existing = User(
        email="existing@example.invalid", password_hash=hash_password("existing-safe-pass"),
        role=Role.MEDICO.value,
    )
    db.add(existing)
    db.commit()
    db.refresh(existing)
    old_hash = existing.password_hash
    result = register_medical_professional(
        db, name="Dr. Existente", email="EXISTING@EXAMPLE.INVALID",
        specialty_ids=[specialty.id],
    )
    assert result.user_id == existing.id
    assert result.temporary_password is None
    assert db.get(User, existing.id).password_hash == old_hash
    assert db.get(Professional, result.professional_id).onboarding_email_status == "NOT_REQUIRED"


def test_other_role_email_and_missing_specialty_are_rejected(db):
    specialty = _specialty(db)
    db.add(User(email="admin@example.invalid", role=Role.ADMINISTRADOR.value, password_hash="test"))
    db.commit()
    with pytest.raises(DirectoryConflictError):
        register_medical_professional(
            db, name="Doctor", email="admin@example.invalid", specialty_ids=[specialty.id]
        )
    with pytest.raises(DirectoryValidationError):
        register_medical_professional(
            db, name="Doctor", email="doc2@example.invalid", specialty_ids=[]
        )
    assert len(db.exec(select(Professional)).all()) == 0


def test_provisional_doctor_cannot_use_clinical_role_until_password_rotation(db):
    specialty = _specialty(db)
    result = register_medical_professional(
        db, name="Dra. Nova", email="nova@example.invalid", specialty_ids=[specialty.id]
    )
    token = create_session(db, user_id=result.user_id, ttl=timedelta(hours=1))
    with pytest.raises(PasswordChangeRequiredError):
        require_role(db, token, Role.MEDICO)
    with pytest.raises(TemporaryPasswordError):
        complete_temporary_password_change(
            db, token=token, current_password="wrong",
            new_password="adequate-new-password-2026",
        )
    complete_temporary_password_change(
        db, token=token, current_password=result.temporary_password,
        new_password="adequate-new-password-2026",
    )
    assert require_role(db, token, Role.MEDICO).id == result.user_id
    assert authenticate_user(db, result.email, result.temporary_password) is None
    assert authenticate_user(db, result.email, "adequate-new-password-2026") is not None
    assert db.get(User, result.user_id).temporary_password_expires_at is None


def test_expired_temporary_password_cannot_be_changed(db):
    specialty = _specialty(db)
    result = register_medical_professional(
        db, name="Expirou", email="expired@example.invalid", specialty_ids=[specialty.id]
    )
    user = db.get(User, result.user_id)
    user.temporary_password_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.add(user)
    db.commit()
    token = create_session(db, user_id=result.user_id, ttl=timedelta(hours=1))
    with pytest.raises(TemporaryPasswordError, match="expirou"):
        complete_temporary_password_change(
            db, token=token, current_password=result.temporary_password,
            new_password="adequate-new-password-2026",
        )


def test_resend_missing_env_does_not_call_provider(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
    def forbidden(*args, **kwargs):
        raise AssertionError("Network must not be called")
    monkeypatch.setattr(httpx, "Client", forbidden)
    result = send_medical_welcome(
        name="QA", email="qa@example.invalid",
        temporary_password="dummy-test-only", professional_id=10,
    )
    assert result.status == "NOT_CONFIGURED"


@pytest.mark.parametrize("response_status,has_id,expected", [
    (200, True, "ACCEPTED"), (422, False, "FAILED"),
    (429, False, "FAILED"), (500, False, "FAILED"), (200, False, "UNKNOWN"),
])
def test_resend_reports_only_actual_provider_acceptance(
    monkeypatch, response_status, has_id, expected
):
    monkeypatch.setenv("RESEND_API_KEY", "fake-unit-test-only")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "qa@example.invalid")
    captured = {}
    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] <= 10.0
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            captured["url"] = url
            captured["kwargs"] = kwargs
            return httpx.Response(
                response_status, json={"id": "fake-resend-id"} if has_id else {}
            )
    monkeypatch.setattr(httpx, "Client", FakeClient)
    result = send_medical_welcome(
        name="<Test>", email="qa@example.invalid",
        temporary_password="dummy-test-only", professional_id=10,
    )
    assert result.status == expected
    assert captured["url"] == "https://api.resend.com/emails"
    assert "Idempotency-Key" in captured["kwargs"]["headers"]
    assert "&lt;Test&gt;" in captured["kwargs"]["json"]["html"]


def test_timeout_is_unknown_not_a_false_failed_or_success(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "fake-unit-test-only")
    monkeypatch.setenv("RESEND_FROM_EMAIL", "qa@example.invalid")
    class TimeoutClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs):
            raise httpx.TimeoutException("fake timeout")
    monkeypatch.setattr(httpx, "Client", TimeoutClient)
    result = send_medical_welcome(
        name="QA", email="qa@example.invalid",
        temporary_password="dummy", professional_id=5,
    )
    assert result.status == "UNKNOWN"
