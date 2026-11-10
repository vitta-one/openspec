"""Idempotent ZapSign orchestration for persisted prescriptions."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from vitta_one.clinical_prescription.service import get_printable_prescription
from vitta_one.integrations.settings import zapsign_settings
from vitta_one.integrations.zapsign import ZapSignClient, ZapSignUnavailableError
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_prescription import Prescription
from vitta_one.models.digital_signature import PrescriptionSignatureRequest, SignatureWebhookEvent
from vitta_one.models.patient_queue import Patient


class SignatureError(ValueError):
    pass


class SignatureNotConfiguredError(SignatureError):
    pass


class SignatureAuthorizationError(PermissionError):
    pass


class SignatureNotFoundError(LookupError):
    pass


class SignatureConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SignatureView:
    id: int
    prescription_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    signed_at: datetime | None
    can_open_signed_document: bool


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _view(row: PrescriptionSignatureRequest) -> SignatureView:
    if row.id is None:
        raise RuntimeError("Solicitação de assinatura persistida sem identificador.")
    return SignatureView(
        id=row.id, prescription_id=row.prescription_id, status=row.status,
        created_at=row.created_at, updated_at=row.updated_at, signed_at=row.signed_at,
        can_open_signed_document=row.status == "SIGNED",
    )


def _markdown(printable) -> str:
    lines = [
        "# Prescrição médica",
        "",
        f"**Paciente:** {printable.patient_name}",
        f"**Profissional:** {printable.professional_name}",
        f"**Registro:** {printable.registration_identifier}",
        f"**Data do atendimento:** {printable.scheduled_at.date().isoformat()}",
        "",
        "## Itens prescritos",
    ]
    for index, item in enumerate(printable.prescription.items, start=1):
        lines.extend(("", f"### {index}. {item.medication_or_item}", item.instructions))
        if item.notes:
            lines.append(f"Observações: {item.notes}")
    if printable.prescription.general_notes:
        lines.extend(("", "## Observações gerais", printable.prescription.general_notes))
    lines.extend(("", "---", "Documento emitido pelo Vitta One para assinatura eletrônica do profissional responsável."))
    return "\n".join(lines)


def get_signature(db: Session, *, prescription_id: int) -> SignatureView | None:
    row = db.exec(select(PrescriptionSignatureRequest).where(PrescriptionSignatureRequest.prescription_id == prescription_id)).first()
    return _view(row) if row else None


def list_patient_signatures(db: Session, *, patient_user_id: int) -> tuple[SignatureView, ...]:
    patient = db.exec(select(Patient).where(Patient.user_id == patient_user_id)).first()
    if patient is None:
        raise SignatureAuthorizationError("O acesso ao portal não possui vínculo clínico.")
    rows = db.exec(
        select(PrescriptionSignatureRequest)
        .join(Prescription, Prescription.id == PrescriptionSignatureRequest.prescription_id)
        .join(ClinicalCareRecord, ClinicalCareRecord.id == Prescription.clinical_care_record_id)
        .where(ClinicalCareRecord.patient_id == patient.id)
        .order_by(PrescriptionSignatureRequest.created_at.desc())
    ).all()
    return tuple(_view(row) for row in rows)


def request_signature(
    db: Session, *, prescription_id: int, doctor_user_id: int,
    client: ZapSignClient | None = None,
) -> SignatureView:
    existing = db.exec(
        select(PrescriptionSignatureRequest)
        .where(PrescriptionSignatureRequest.prescription_id == prescription_id)
        .with_for_update()
    ).first()
    if existing is not None:
        return _view(existing)

    printable = get_printable_prescription(db, prescription_id=prescription_id, doctor_user_id=doctor_user_id)
    identity = db.get(User, doctor_user_id)
    if identity is None or not identity.email:
        raise SignatureAuthorizationError("O Médico não possui identidade válida para assinatura.")
    settings = zapsign_settings()
    if settings is None:
        raise SignatureNotConfiguredError("A assinatura digital ainda não está configurada.")
    request_key = hashlib.sha256(f"prescription:{prescription_id}".encode()).hexdigest()
    external_id = f"vitta-prescription-{prescription_id}"
    row = PrescriptionSignatureRequest(
        prescription_id=prescription_id, requested_by_user_id=doctor_user_id,
        request_key=request_key, external_id=external_id, signer_email=identity.email,
        status="CREATING",
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        concurrent = db.exec(select(PrescriptionSignatureRequest).where(PrescriptionSignatureRequest.prescription_id == prescription_id)).first()
        if concurrent is None:
            raise SignatureConflictError("Não foi possível iniciar a assinatura.")
        return _view(concurrent)
    db.refresh(row)

    provider = client or ZapSignClient(settings)
    try:
        document = provider.create_document(
            name=f"Prescrição {prescription_id}", markdown_text=_markdown(printable),
            external_id=external_id, signer_name=printable.professional_name,
            signer_email=identity.email,
        )
    except ZapSignUnavailableError:
        locked = db.exec(select(PrescriptionSignatureRequest).where(PrescriptionSignatureRequest.id == row.id).with_for_update()).one()
        locked.status = "RECONCILIATION_REQUIRED"
        locked.status_detail_code = "CREATE_RESULT_UNKNOWN"
        locked.updated_at = utc_now()
        db.add(locked)
        db.commit()
        raise

    locked = db.exec(select(PrescriptionSignatureRequest).where(PrescriptionSignatureRequest.id == row.id).with_for_update()).one()
    locked.provider_document_token = document.token
    locked.provider_signer_token = document.signer_token
    locked.status = "SIGNED" if document.status.lower() == "signed" else "PENDING"
    locked.status_detail_code = ""
    locked.last_provider_sync_at = utc_now()
    locked.updated_at = locked.last_provider_sync_at
    if locked.status == "SIGNED":
        locked.signed_at = locked.updated_at
    db.add(locked)
    db.commit()
    db.refresh(locked)
    return _view(locked)


_TERMINAL = {"SIGNED", "REFUSED", "EXPIRED", "CANCELLED"}
_EVENT_STATUS = {
    "doc_created": "PENDING", "doc_refused": "REFUSED", "doc_expired": "EXPIRED",
    "doc_deleted": "CANCELLED",
}


def _event_id(payload: dict) -> str:
    supplied = str(payload.get("event_id") or payload.get("id") or "").strip()
    if supplied:
        return supplied[:160]
    stable = {
        "event_type": payload.get("event_type"), "token": payload.get("token"),
        "status": payload.get("status"), "last_update_at": payload.get("last_update_at"),
        "signer": (payload.get("signer_who_signed") or {}).get("token"),
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def process_zapsign_webhook(db: Session, payload: dict) -> str:
    if not isinstance(payload, dict):
        raise SignatureError("Payload de webhook inválido.")
    event_type = str(payload.get("event_type") or "").strip()
    token = str(payload.get("token") or "").strip()
    if not re.fullmatch(r"[a-z_]{3,64}", event_type) or not token or len(token) > 128:
        raise SignatureError("Payload de webhook inválido.")
    event_id = _event_id(payload)
    if db.exec(select(SignatureWebhookEvent.id).where(SignatureWebhookEvent.event_id == event_id)).first() is not None:
        return "DUPLICATE"
    event = SignatureWebhookEvent(event_id=event_id, event_type=event_type, provider_document_token=token)
    db.add(event)
    request = db.exec(
        select(PrescriptionSignatureRequest)
        .where(PrescriptionSignatureRequest.provider_document_token == token)
        .with_for_update()
    ).first()
    if request is None:
        event.outcome = "UNKNOWN_DOCUMENT"
        event.processed_at = utc_now()
        db.add(event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return "DUPLICATE"
        return event.outcome
    new_status = _EVENT_STATUS.get(event_type)
    if event_type == "doc_signed":
        new_status = "SIGNED" if str(payload.get("status") or "").lower() == "signed" else "PENDING"
    if new_status is None:
        event.outcome = "IGNORED"
    elif request.status in _TERMINAL and request.status != new_status:
        event.outcome = "STALE"
    else:
        request.status = new_status
        request.updated_at = utc_now()
        request.last_provider_sync_at = request.updated_at
        if new_status == "SIGNED" and request.signed_at is None:
            request.signed_at = request.updated_at
        db.add(request)
        event.outcome = "PROCESSED"
    event.processed_at = utc_now()
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return "DUPLICATE"
    except SQLAlchemyError as exc:
        db.rollback()
        raise SignatureConflictError("Não foi possível processar o evento de assinatura.") from exc
    return event.outcome


def signed_document_url(
    db: Session, *, prescription_id: int, actor_user_id: int, actor_is_patient: bool,
    client: ZapSignClient | None = None,
) -> str:
    request = db.exec(select(PrescriptionSignatureRequest).where(PrescriptionSignatureRequest.prescription_id == prescription_id)).first()
    if request is None or request.status != "SIGNED" or not request.provider_document_token:
        raise SignatureNotFoundError("O documento assinado ainda não está disponível.")
    prescription = db.get(Prescription, prescription_id)
    if prescription is None:
        raise SignatureNotFoundError("A Prescrição não está disponível.")
    if actor_is_patient:
        record = db.get(ClinicalCareRecord, prescription.clinical_care_record_id)
        patient = db.exec(select(Patient).where(Patient.user_id == actor_user_id)).first()
        if record is None or patient is None or record.patient_id != patient.id:
            raise SignatureAuthorizationError("O documento não está disponível para este acesso.")
    elif prescription.doctor_user_id != actor_user_id:
        raise SignatureAuthorizationError("O documento pertence a outro profissional.")
    settings = zapsign_settings()
    if settings is None:
        raise SignatureNotConfiguredError("A assinatura digital ainda não está configurada.")
    provider = client or ZapSignClient(settings)
    document = provider.get_document(request.provider_document_token)
    if document.status.lower() != "signed" or not document.signed_file:
        raise SignatureNotFoundError("O documento assinado ainda não está disponível.")
    return document.signed_file

