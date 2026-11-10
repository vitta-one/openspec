"""Clinical attachment rules, provider orchestration and safe projections."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import PurePath
import re
import secrets

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from vitta_one.integrations.cloudinary import CloudinaryClient, CloudinaryUnavailableError
from vitta_one.integrations.settings import cloudinary_settings
from vitta_one.models.appointment import Consultation
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_documents import ClinicalAttachment, ClinicalAttachmentAudit
from vitta_one.models.patient_queue import Patient


ALLOWED_CONTENT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}
TITLE_LIMIT = 160
CATEGORY_LIMIT = 40


class AttachmentError(ValueError):
    pass


class AttachmentNotConfiguredError(AttachmentError):
    pass


class AttachmentAuthorizationError(PermissionError):
    pass


class AttachmentNotFoundError(LookupError):
    pass


class AttachmentConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AttachmentView:
    id: int
    patient_id: int
    clinical_care_record_id: int | None
    title: str
    category: str
    exam_date: date | None
    original_filename: str
    content_type: str
    byte_size: int
    patient_visible: bool
    status: str
    created_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_text(value: str, *, label: str, limit: int) -> str:
    cleaned = " ".join(str(value or "").split())
    if not cleaned:
        raise AttachmentError(f"Informe {label}.")
    if len(cleaned) > limit:
        raise AttachmentError(f"{label.capitalize()} excede o limite de {limit} caracteres.")
    return cleaned


def _filename(value: str) -> str:
    raw = str(value or "").strip()
    name = PurePath(raw.replace("\\", "/")).name
    if not name or name in {".", ".."} or len(name) > 255 or not re.fullmatch(r"[\w.()\- ]+", name, re.UNICODE):
        raise AttachmentError("O nome do arquivo é inválido.")
    if PurePath(name).suffix.lower() not in ALLOWED_SUFFIXES:
        raise AttachmentError("Envie um arquivo PDF, JPEG ou PNG.")
    return name


def _view(row: ClinicalAttachment) -> AttachmentView:
    if row.id is None:
        raise RuntimeError("Anexo persistido sem identificador.")
    return AttachmentView(
        id=row.id, patient_id=row.patient_id, clinical_care_record_id=row.clinical_care_record_id,
        title=row.title, category=row.category, exam_date=row.exam_date,
        original_filename=row.original_filename, content_type=row.content_type,
        byte_size=row.byte_size, patient_visible=row.patient_visible, status=row.status,
        created_at=row.created_at,
    )


def _doctor_record(db: Session, *, record_id: int, doctor_user_id: int, lock: bool) -> ClinicalCareRecord:
    stmt = select(ClinicalCareRecord).where(ClinicalCareRecord.id == record_id)
    if lock:
        stmt = stmt.with_for_update()
    record = db.exec(stmt).first()
    if record is None:
        raise AttachmentNotFoundError("O Atendimento clínico não está disponível.")
    if record.doctor_user_id != doctor_user_id:
        raise AttachmentAuthorizationError("O Atendimento pertence a outro profissional.")
    if record.consultation_id is not None:
        consultation = db.get(Consultation, record.consultation_id)
        if consultation is None or consultation.patient_id != record.patient_id:
            raise AttachmentNotFoundError("O contexto clínico está inconsistente.")
    return record


def create_attachment(
    db: Session, *, doctor_user_id: int, clinical_care_record_id: int, title: str,
    category: str, exam_date: date | None, filename: str, content_type: str,
    content: bytes, client: CloudinaryClient | None = None,
) -> AttachmentView:
    record = _doctor_record(db, record_id=clinical_care_record_id, doctor_user_id=doctor_user_id, lock=True)
    clean_title = _clean_text(title, label="o título", limit=TITLE_LIMIT)
    clean_category = _clean_text(category, label="a categoria", limit=CATEGORY_LIMIT).upper().replace(" ", "_")
    clean_filename = _filename(filename)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise AttachmentError("O tipo do arquivo não é permitido.")
    settings = cloudinary_settings()
    if settings is None:
        raise AttachmentNotConfiguredError("O armazenamento de anexos ainda não está configurado.")
    if not content or len(content) > settings.max_bytes:
        raise AttachmentError(f"O arquivo deve ter entre 1 e {settings.max_bytes} bytes.")
    provider = client or CloudinaryClient(settings)
    asset = provider.upload(content=content, filename=clean_filename, public_id=secrets.token_hex(20))
    if asset.bytes != len(content):
        try:
            provider.delete(public_id=asset.public_id, resource_type=asset.resource_type)
        finally:
            raise AttachmentConflictError("O armazenamento não confirmou o tamanho integral do arquivo.")
    attachment = ClinicalAttachment(
        patient_id=record.patient_id, consultation_id=record.consultation_id,
        clinical_care_record_id=record.id, uploaded_by_user_id=doctor_user_id,
        title=clean_title, category=clean_category, exam_date=exam_date,
        original_filename=clean_filename, content_type=content_type, byte_size=len(content),
        cloud_asset_id=asset.asset_id, cloud_public_id=asset.public_id,
        cloud_version=asset.version, cloud_resource_type=asset.resource_type,
        cloud_format=asset.format, status="ACTIVE", patient_visible=False,
    )
    db.add(attachment)
    try:
        db.flush()
        db.add(ClinicalAttachmentAudit(attachment_id=attachment.id, actor_user_id=doctor_user_id, action="UPLOAD", outcome="SUCCESS"))
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            provider.delete(public_id=asset.public_id, resource_type=asset.resource_type)
        except CloudinaryUnavailableError:
            pass
        raise AttachmentConflictError("Não foi possível concluir o cadastro do anexo.") from exc
    db.refresh(attachment)
    return _view(attachment)


def list_doctor_attachments(db: Session, *, doctor_user_id: int, clinical_care_record_id: int) -> tuple[AttachmentView, ...]:
    _doctor_record(db, record_id=clinical_care_record_id, doctor_user_id=doctor_user_id, lock=False)
    rows = db.exec(
        select(ClinicalAttachment).where(
            ClinicalAttachment.clinical_care_record_id == clinical_care_record_id,
            ClinicalAttachment.status != "REMOVED",
        ).order_by(ClinicalAttachment.created_at.desc(), ClinicalAttachment.id.desc())
    ).all()
    return tuple(_view(row) for row in rows)


def list_patient_attachments(db: Session, *, patient_user_id: int) -> tuple[AttachmentView, ...]:
    patient = db.exec(select(Patient).where(Patient.user_id == patient_user_id)).first()
    if patient is None:
        raise AttachmentAuthorizationError("O acesso ao portal não possui vínculo clínico.")
    rows = db.exec(
        select(ClinicalAttachment).where(
            ClinicalAttachment.patient_id == patient.id,
            ClinicalAttachment.patient_visible.is_(True),
            ClinicalAttachment.status == "ACTIVE",
        ).order_by(ClinicalAttachment.created_at.desc(), ClinicalAttachment.id.desc())
    ).all()
    return tuple(_view(row) for row in rows)


def set_patient_visibility(db: Session, *, attachment_id: int, doctor_user_id: int, visible: bool) -> AttachmentView:
    row = db.exec(select(ClinicalAttachment).where(ClinicalAttachment.id == attachment_id).with_for_update()).first()
    if row is None or row.status == "REMOVED":
        raise AttachmentNotFoundError("O anexo não está disponível.")
    if row.clinical_care_record_id is None:
        raise AttachmentAuthorizationError("O anexo não possui Atendimento autorizado.")
    _doctor_record(db, record_id=row.clinical_care_record_id, doctor_user_id=doctor_user_id, lock=True)
    row.patient_visible = bool(visible)
    row.updated_at = utc_now()
    db.add(row)
    db.add(ClinicalAttachmentAudit(attachment_id=row.id, actor_user_id=doctor_user_id, action="RELEASE" if visible else "REVOKE", outcome="SUCCESS"))
    db.commit()
    db.refresh(row)
    return _view(row)


def attachment_download_url(
    db: Session, *, attachment_id: int, actor_user_id: int, actor_is_patient: bool,
    client: CloudinaryClient | None = None,
) -> str:
    row = db.get(ClinicalAttachment, attachment_id)
    if row is None or row.status != "ACTIVE":
        raise AttachmentNotFoundError("O anexo não está disponível.")
    if actor_is_patient:
        patient = db.exec(select(Patient).where(Patient.user_id == actor_user_id)).first()
        if patient is None or patient.id != row.patient_id or not row.patient_visible:
            raise AttachmentAuthorizationError("O anexo não está disponível para este acesso.")
    else:
        if row.clinical_care_record_id is None:
            raise AttachmentAuthorizationError("O anexo não possui Atendimento autorizado.")
        _doctor_record(db, record_id=row.clinical_care_record_id, doctor_user_id=actor_user_id, lock=False)
    settings = cloudinary_settings()
    if settings is None:
        raise AttachmentNotConfiguredError("O armazenamento de anexos ainda não está configurado.")
    provider = client or CloudinaryClient(settings)
    url = provider.private_download_url(public_id=row.cloud_public_id, format=row.cloud_format, resource_type=row.cloud_resource_type)
    db.add(ClinicalAttachmentAudit(attachment_id=row.id, actor_user_id=actor_user_id, action="DOWNLOAD", outcome="SUCCESS"))
    db.commit()
    return url


def remove_attachment(db: Session, *, attachment_id: int, doctor_user_id: int, client: CloudinaryClient | None = None) -> None:
    row = db.exec(select(ClinicalAttachment).where(ClinicalAttachment.id == attachment_id).with_for_update()).first()
    if row is None or row.status == "REMOVED":
        raise AttachmentNotFoundError("O anexo não está disponível.")
    if row.clinical_care_record_id is None:
        raise AttachmentAuthorizationError("O anexo não possui Atendimento autorizado.")
    _doctor_record(db, record_id=row.clinical_care_record_id, doctor_user_id=doctor_user_id, lock=True)
    settings = cloudinary_settings()
    if settings is None:
        raise AttachmentNotConfiguredError("O armazenamento de anexos ainda não está configurado.")
    provider = client or CloudinaryClient(settings)
    try:
        provider.delete(public_id=row.cloud_public_id, resource_type=row.cloud_resource_type)
    except CloudinaryUnavailableError:
        row.status = "DELETION_FAILED"
        row.updated_at = utc_now()
        db.add(row)
        db.add(ClinicalAttachmentAudit(attachment_id=row.id, actor_user_id=doctor_user_id, action="DELETE", outcome="FAILED", detail_code="PROVIDER_UNAVAILABLE"))
        db.commit()
        raise
    row.status = "REMOVED"
    row.patient_visible = False
    row.removed_at = utc_now()
    row.updated_at = row.removed_at
    db.add(row)
    db.add(ClinicalAttachmentAudit(attachment_id=row.id, actor_user_id=doctor_user_id, action="DELETE", outcome="SUCCESS"))
    db.commit()

