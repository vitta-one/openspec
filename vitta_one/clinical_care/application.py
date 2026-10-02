"""Authorized application boundary for clinical care records."""

from sqlmodel import Session

from vitta_one.admin_preview.service import require_local_admin_preview
from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.clinical_care.service import (
    ClinicalCareRecordItem,
    ClinicalHistoryPage,
    get_active_record,
    list_completed_history_for_patient,
    list_history_for_active_entry,
    save_active_record,
)


def doctor_get_active_record(
    db: Session,
    *,
    token: str,
    entry_id: int,
) -> ClinicalCareRecordItem:
    identity = require_role(db, token, Role.MEDICO)
    return get_active_record(
        db,
        entry_id=entry_id,
        doctor_user_id=identity.id,
    )


def doctor_save_active_record(
    db: Session,
    *,
    token: str,
    entry_id: int,
    chief_complaint: str,
    anamnesis: str,
    diagnosis: str,
    conduct_notes: str,
) -> ClinicalCareRecordItem:
    identity = require_role(db, token, Role.MEDICO)
    return save_active_record(
        db,
        entry_id=entry_id,
        doctor_user_id=identity.id,
        chief_complaint=chief_complaint,
        anamnesis=anamnesis,
        diagnosis=diagnosis,
        conduct_notes=conduct_notes,
    )


def doctor_list_active_patient_history(
    db: Session,
    *,
    token: str,
    entry_id: int,
    page: int = 1,
) -> ClinicalHistoryPage:
    identity = require_role(db, token, Role.MEDICO)
    return list_history_for_active_entry(
        db,
        entry_id=entry_id,
        doctor_user_id=identity.id,
        page=page,
    )


def admin_preview_patient_history(
    db: Session,
    *,
    token: str,
    patient_id: int,
    page: int = 1,
) -> ClinicalHistoryPage:
    require_local_admin_preview(db, token)
    return list_completed_history_for_patient(db, patient_id=patient_id, page=page)
