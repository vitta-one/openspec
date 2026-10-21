"""Explicitly isolated local QA account provisioning — never a production onboarding path.

The normal physician and patient e-mail invitation flows remain unchanged.
Passwords from QA forms are only processed in the event handler, Argon2id-hashed,
and never assigned to Reflex State, logged, or sent to a mail provider.
"""

import os

from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password, is_valid_email_identifier, normalize_email
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient


class LocalQaAccountError(ValueError):
    """Safe validation or duplicate-identity error for local demonstration."""


def local_qa_enabled() -> bool:
    """Fail closed: preview opt-in + dedicated database + local service and public URL."""
    if os.getenv("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "").strip().lower() != "true":
        return False
    public_url = os.getenv("VITTA_ONE_PUBLIC_URL", "").strip().rstrip("/")
    if public_url not in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        return False
    try:
        url = make_url(os.environ.get("DATABASE_URL", ""))
    except (ValueError, KeyError):
        return False
    return (
        url.drivername == "postgresql+psycopg"
        and url.host in {"localhost", "127.0.0.1"}
        and url.database == "vitta_one_qa"
        and url.port in {5432, 5433, 55432}
    )


def _verify_local_qa() -> None:
    if not local_qa_enabled():
        raise LocalQaAccountError(
            "Contas de demonstração só podem ser criadas no ambiente QA local isolado."
        )


def _validate_qa_credentials(email: str, password: str) -> str:
    normalized = normalize_email(str(email or ""))
    if not is_valid_email_identifier(normalized) or "." not in normalized.rsplit("@", 1)[1]:
        raise LocalQaAccountError("Informe um e-mail de login válido.")
    if not 12 <= len(password) <= 128:
        raise LocalQaAccountError("A senha de QA precisa ter entre 12 e 128 caracteres.")
    return normalized


def admin_create_qa_receptionist(
    db: Session, *, token: str, email: str, password: str
) -> User:
    """Allow Administrator to create a separate receptionist login in local QA."""
    require_role(db, token, Role.ADMINISTRADOR)
    _verify_local_qa()
    normalized = _validate_qa_credentials(email, password)
    if db.exec(select(User).where(User.email == normalized)).first() is not None:
        raise LocalQaAccountError("Este e-mail já possui um usuário.")
    user = User(
        email=normalized, role=Role.RECEPCIONISTA.value,
        password_hash=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LocalQaAccountError("Este e-mail já possui um usuário.") from exc
    db.refresh(user)
    return user


def reception_activate_qa_patient(
    db: Session, *, token: str, patient_id: int,
    email: str, password: str, consent_confirmed: bool
) -> User:
    """Link a selected registered patient to a login, only in local QA."""
    require_role(db, token, Role.RECEPCIONISTA)
    _verify_local_qa()
    if consent_confirmed is not True:
        raise LocalQaAccountError("Confirme o consentimento do paciente.")
    normalized = _validate_qa_credentials(email, password)
    patient = db.exec(
        select(Patient).where(Patient.id == patient_id).with_for_update()
    ).first()
    if patient is None:
        raise LocalQaAccountError("Cadastre ou localize o paciente primeiro.")
    if patient.user_id is not None:
        raise LocalQaAccountError("O paciente já possui acesso ao portal.")
    if db.exec(select(User).where(User.email == normalized)).first() is not None:
        raise LocalQaAccountError("Este e-mail já possui um usuário.")
    user = User(
        email=normalized, role=Role.PACIENTE.value,
        password_hash=hash_password(password),
    )
    db.add(user)
    try:
        db.flush()
        patient.user_id = user.id
        db.add(patient)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LocalQaAccountError("Não foi possível vincular o acesso ao paciente.") from exc
    db.refresh(user)
    return user
