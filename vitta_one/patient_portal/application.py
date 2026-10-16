"""Authorized reception operations for patient portal invitations."""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, select

from vitta_one.auth.authorization import (
    PasswordChangeRequiredError,
    RoleForbiddenError,
    require_authenticated,
)
from vitta_one.auth.roles import Role
from vitta_one.models.patient_queue import Patient, PatientPortalInvitation
from vitta_one.patient_portal.service import (
    PatientPortalError,
    create_patient_invitation,
)
from vitta_one.professional_directory.email_sender import EmailDelivery


@dataclass(frozen=True, slots=True)
class PatientPortalStatus:
    state: str
    label: str


def _require_reception_or_admin(db: Session, token: str):
    identity = require_authenticated(db, token)
    if identity.role not in {Role.RECEPCIONISTA, Role.ADMINISTRADOR}:
        raise RoleForbiddenError(identity, Role.RECEPCIONISTA)
    if identity.must_change_password:
        raise PasswordChangeRequiredError("Troca de senha inicial obrigatória.")
    return identity


def reception_get_patient_portal_status(
    db: Session, *, token: str, patient_id: int
) -> PatientPortalStatus:
    _require_reception_or_admin(db, token)
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise PatientPortalError("O cadastro do paciente não está disponível.")
    if patient.user_id is not None:
        return PatientPortalStatus("ATIVO", "Acesso ao portal ativo")
    latest = db.exec(
        select(PatientPortalInvitation)
        .where(PatientPortalInvitation.patient_id == patient_id)
        .order_by(PatientPortalInvitation.created_at.desc(), PatientPortalInvitation.id.desc())
    ).first()
    expiration = latest.expires_at if latest is not None else None
    if expiration is not None and expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=timezone.utc)
    if latest is None or latest.revoked_at is not None or expiration <= datetime.now(timezone.utc):
        return PatientPortalStatus("SEM_PORTAL", "Sem acesso ao portal")
    if latest.delivery_status == "ACCEPTED":
        return PatientPortalStatus("CONVITE_ENVIADO", "Convite enviado; aguardando ativação")
    if latest.delivery_status == "UNKNOWN":
        return PatientPortalStatus("ENVIO_INDETERMINADO", "Envio sem confirmação; solicite novo convite se necessário")
    return PatientPortalStatus("PENDENTE", "Convite pendente de envio")


def reception_issue_patient_invitation(
    db: Session,
    *,
    token: str,
    patient_id: int,
    email: str,
    consent_confirmed: bool,
) -> tuple[PatientPortalStatus, EmailDelivery]:
    identity = _require_reception_or_admin(db, token)
    invitation, delivery = create_patient_invitation(
        db,
        patient_id=patient_id,
        email=email,
        created_by_user_id=identity.id,
        consent_confirmed=consent_confirmed,
    )
    if delivery.status == "ACCEPTED":
        label = "Convite enviado; aguardando ativação"
    elif delivery.status == "UNKNOWN":
        label = "Envio sem confirmação; solicite novo convite se necessário"
    else:
        label = "Envio indisponível; nenhum acesso foi ativado"
    # Do not serialize the invitation, address or hash into Reflex State.
    return PatientPortalStatus(delivery.status, label), delivery
