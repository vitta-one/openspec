"""Patient activation and invitation domain services."""

from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.roles import Role
from vitta_one.auth.security import (
    hash_password,
    is_valid_email_identifier,
    normalize_email,
)
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, PatientPortalInvitation
from vitta_one.patient_portal.settings import patient_activation_url
from vitta_one.professional_directory.email_sender import (
    EmailDelivery,
    send_patient_portal_invitation,
)


class PatientPortalError(ValueError):
    """A safe operational error for invitation and activation flows."""


class PatientPortalActivationError(PatientPortalError):
    """Generic public activation failure; it never reveals account existence."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _normalize_invite_email(email: str) -> str:
    value = normalize_email(str(email or ""))
    if not _valid_patient_email(value):
        raise PatientPortalError("Informe um e-mail válido para o convite.")
    return value


def _valid_patient_email(value: str) -> bool:
    if not is_valid_email_identifier(value):
        return False
    local, domain = value.rsplit("@", 1)
    if len(local) > 64 or len(domain) > 253 or "." not in domain:
        return False
    if local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    return all(
        label and len(label) <= 63 and not label.startswith("-") and not label.endswith("-")
        and bool(re.fullmatch(r"[a-z0-9-]+", label))
        for label in domain.split(".")
    )


def create_patient_invitation(
    db: Session,
    *,
    patient_id: int,
    email: str,
    created_by_user_id: int,
    consent_confirmed: bool,
    now: datetime | None = None,
) -> tuple[PatientPortalInvitation, EmailDelivery]:
    """Issue a fresh one-time code only after a distinct consented action."""
    if consent_confirmed is not True:
        raise PatientPortalError("Confirme o consentimento antes de enviar o convite.")
    normalized_email = _normalize_invite_email(email)
    timestamp = _as_utc(now or utc_now())
    patient = db.exec(
        select(Patient).where(Patient.id == patient_id).with_for_update()
    ).first()
    if patient is None:
        raise PatientPortalError("O cadastro do paciente não está disponível.")
    if patient.user_id is not None:
        raise PatientPortalError("Este cadastro já possui acesso ao portal.")
    # Recuse emails already owned by another account before issuing a token.
    if db.exec(select(User.id).where(User.email == normalized_email)).first() is not None:
        raise PatientPortalError("O e-mail informado já está vinculado a uma conta.")
    other_invitation = db.exec(
        select(PatientPortalInvitation)
        .where(
            PatientPortalInvitation.email == normalized_email,
            PatientPortalInvitation.patient_id != patient_id,
            PatientPortalInvitation.consumed_at.is_(None),
            PatientPortalInvitation.revoked_at.is_(None),
            PatientPortalInvitation.expires_at > timestamp,
        )
    ).first()
    if other_invitation is not None:
        raise PatientPortalError("Este e-mail já possui um convite de ativação em andamento.")

    latest = db.exec(
        select(PatientPortalInvitation)
        .where(PatientPortalInvitation.patient_id == patient_id)
        .order_by(PatientPortalInvitation.created_at.desc(), PatientPortalInvitation.id.desc())
    ).first()
    if latest is not None and timestamp < _as_utc(latest.created_at) + timedelta(minutes=2):
        raise PatientPortalError("Aguarde 2 minutos antes de enviar outro convite.")

    active = db.exec(
        select(PatientPortalInvitation)
        .where(
            PatientPortalInvitation.patient_id == patient_id,
            PatientPortalInvitation.consumed_at.is_(None),
            PatientPortalInvitation.revoked_at.is_(None),
            PatientPortalInvitation.expires_at > timestamp,
        )
        .with_for_update()
    ).all()
    for previous in active:
        previous.revoked_at = timestamp
        previous.delivery_status = "REVOKED"
        db.add(previous)

    code = secrets.token_urlsafe(32)
    invitation = PatientPortalInvitation(
        patient_id=patient_id,
        email=normalized_email,
        code_hash=_code_hash(code),
        created_by_user_id=created_by_user_id,
        consented_at=timestamp,
        created_at=timestamp,
        expires_at=timestamp + timedelta(hours=24),
        delivery_status="PENDING",
    )
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PatientPortalError("Não foi possível preparar o convite. Tente novamente.") from exc
    db.refresh(invitation)

    activation_url = patient_activation_url()
    delivery = send_patient_portal_invitation(
        name=patient.name,
        email=normalized_email,
        code=code,
        activation_url=activation_url,
        invitation_id=invitation.id,
    )
    invitation.delivery_status = delivery.status
    invitation.provider_message_id = delivery.message_id
    if delivery.status == "ACCEPTED":
        invitation.sent_at = utc_now()
    elif delivery.status in {"NOT_CONFIGURED", "FAILED"}:
        invitation.revoked_at = utc_now()
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    # The plaintext code is not returned from this service or persisted anywhere.
    return invitation, delivery


def activate_patient_account(
    db: Session,
    *,
    email: str,
    code: str,
    password: str,
    now: datetime | None = None,
) -> User:
    """Consume a valid code once and atomically create/link a PACIENTE account."""
    timestamp = _as_utc(now or utc_now())
    generic_error = PatientPortalActivationError(
        "Não foi possível ativar este acesso. Confira os dados ou solicite um novo convite à Recepção."
    )
    normalized_email = normalize_email(str(email or ""))
    secret = str(code or "").strip()
    new_password = str(password or "")
    if (
        not _valid_patient_email(normalized_email)
        or not secret
        or len(secret) > 128
        or len(new_password) < 12
        or len(new_password) > 128
    ):
        raise generic_error

    invitation = db.exec(
        select(PatientPortalInvitation)
        .where(
            PatientPortalInvitation.email == normalized_email,
            PatientPortalInvitation.code_hash == _code_hash(secret),
        )
        .with_for_update()
    ).first()
    if invitation is None:
        raise generic_error
    if (
        invitation.consented_at is None
        or invitation.revoked_at is not None
        or invitation.consumed_at is not None
        or _as_utc(invitation.expires_at) <= timestamp
        or invitation.delivery_status not in {"ACCEPTED", "UNKNOWN"}
    ):
        raise generic_error

    patient = db.exec(
        select(Patient).where(Patient.id == invitation.patient_id).with_for_update()
    ).first()
    if patient is None or patient.user_id is not None:
        raise generic_error
    if db.exec(select(User).where(User.email == normalized_email)).first() is not None:
        raise generic_error

    identity = User(
        email=normalized_email,
        password_hash=hash_password(new_password),
        role=Role.PACIENTE.value,
    )
    db.add(identity)
    db.flush()
    patient.user_id = identity.id
    invitation.consumed_at = timestamp
    db.add(patient)
    db.add(invitation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise generic_error from exc
    db.refresh(identity)
    return identity
