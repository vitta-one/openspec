"""Authenticated application boundary for clinical attachments."""

from datetime import date

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from .service import (
    AttachmentView, attachment_download_url, create_attachment, list_doctor_attachments,
    list_patient_attachments, remove_attachment, set_patient_visibility,
)


def doctor_upload_attachment(db: Session, *, token: str, clinical_care_record_id: int, title: str, category: str, exam_date: date | None, filename: str, content_type: str, content: bytes, client=None) -> AttachmentView:
    identity = require_role(db, token, Role.MEDICO)
    return create_attachment(
        db, doctor_user_id=identity.id, clinical_care_record_id=clinical_care_record_id,
        title=title, category=category, exam_date=exam_date, filename=filename,
        content_type=content_type, content=content, client=client,
    )


def doctor_list_attachments(db: Session, *, token: str, clinical_care_record_id: int) -> tuple[AttachmentView, ...]:
    identity = require_role(db, token, Role.MEDICO)
    return list_doctor_attachments(db, doctor_user_id=identity.id, clinical_care_record_id=clinical_care_record_id)


def doctor_set_attachment_visibility(db: Session, *, token: str, attachment_id: int, visible: bool) -> AttachmentView:
    identity = require_role(db, token, Role.MEDICO)
    return set_patient_visibility(db, attachment_id=attachment_id, doctor_user_id=identity.id, visible=visible)


def doctor_attachment_download(db: Session, *, token: str, attachment_id: int, client=None) -> str:
    identity = require_role(db, token, Role.MEDICO)
    return attachment_download_url(db, attachment_id=attachment_id, actor_user_id=identity.id, actor_is_patient=False, client=client)


def patient_list_attachments(db: Session, *, token: str) -> tuple[AttachmentView, ...]:
    identity = require_role(db, token, Role.PACIENTE)
    return list_patient_attachments(db, patient_user_id=identity.id)


def patient_attachment_download(db: Session, *, token: str, attachment_id: int, client=None) -> str:
    identity = require_role(db, token, Role.PACIENTE)
    return attachment_download_url(db, attachment_id=attachment_id, actor_user_id=identity.id, actor_is_patient=True, client=client)


def doctor_remove_attachment(db: Session, *, token: str, attachment_id: int, client=None) -> None:
    identity = require_role(db, token, Role.MEDICO)
    remove_attachment(db, attachment_id=attachment_id, doctor_user_id=identity.id, client=client)
