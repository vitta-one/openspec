"""Authenticated application boundary for prescription signatures."""

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from .service import SignatureView, list_patient_signatures, request_signature, signed_document_url


def doctor_request_signature(db: Session, *, token: str, prescription_id: int, client=None) -> SignatureView:
    identity = require_role(db, token, Role.MEDICO)
    return request_signature(db, prescription_id=prescription_id, doctor_user_id=identity.id, client=client)


def doctor_signed_document_url(db: Session, *, token: str, prescription_id: int, client=None) -> str:
    identity = require_role(db, token, Role.MEDICO)
    return signed_document_url(db, prescription_id=prescription_id, actor_user_id=identity.id, actor_is_patient=False, client=client)


def patient_signed_document_url(db: Session, *, token: str, prescription_id: int, client=None) -> str:
    identity = require_role(db, token, Role.PACIENTE)
    return signed_document_url(db, prescription_id=prescription_id, actor_user_id=identity.id, actor_is_patient=True, client=client)


def patient_signature_requests(db: Session, *, token: str) -> tuple[SignatureView, ...]:
    identity = require_role(db, token, Role.PACIENTE)
    return list_patient_signatures(db, patient_user_id=identity.id)
