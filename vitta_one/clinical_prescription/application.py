"""Authorized application boundary for clinical prescriptions."""

from sqlmodel import Session

from vitta_one.admin_preview.service import require_local_admin_preview
from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.clinical_prescription.service import (
    PrescriptionView,
    PrintablePrescriptionView,
    add_prescription_item,
    create_prescription,
    delete_prescription,
    get_printable_prescription,
    list_current_prescriptions,
    list_prescriptions_for_records,
    remove_prescription_item,
    update_prescription_item,
    update_prescription_notes,
)


def doctor_list_current_prescriptions(
    db: Session,
    *,
    token: str,
    clinical_care_record_id: int,
) -> tuple[PrescriptionView, ...]:
    identity = require_role(db, token, Role.MEDICO)
    return list_current_prescriptions(
        db,
        clinical_care_record_id=clinical_care_record_id,
        doctor_user_id=identity.id,
    )


def doctor_create_prescription(
    db: Session,
    *,
    token: str,
    clinical_care_record_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
    general_notes: str = "",
) -> PrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return create_prescription(
        db,
        clinical_care_record_id=clinical_care_record_id,
        doctor_user_id=identity.id,
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
        general_notes=general_notes,
    )


def doctor_add_prescription_item(
    db: Session,
    *,
    token: str,
    prescription_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
) -> PrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return add_prescription_item(
        db,
        prescription_id=prescription_id,
        doctor_user_id=identity.id,
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
    )


def doctor_update_prescription_item(
    db: Session,
    *,
    token: str,
    prescription_id: int,
    item_id: int,
    medication_or_item: str,
    instructions: str,
    notes: str = "",
) -> PrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return update_prescription_item(
        db,
        prescription_id=prescription_id,
        item_id=item_id,
        doctor_user_id=identity.id,
        medication_or_item=medication_or_item,
        instructions=instructions,
        notes=notes,
    )


def doctor_remove_prescription_item(
    db: Session,
    *,
    token: str,
    prescription_id: int,
    item_id: int,
) -> PrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return remove_prescription_item(
        db,
        prescription_id=prescription_id,
        item_id=item_id,
        doctor_user_id=identity.id,
    )


def doctor_update_prescription_notes(
    db: Session,
    *,
    token: str,
    prescription_id: int,
    general_notes: str,
) -> PrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return update_prescription_notes(
        db,
        prescription_id=prescription_id,
        doctor_user_id=identity.id,
        general_notes=general_notes,
    )


def doctor_delete_prescription(
    db: Session,
    *,
    token: str,
    prescription_id: int,
) -> None:
    identity = require_role(db, token, Role.MEDICO)
    delete_prescription(
        db,
        prescription_id=prescription_id,
        doctor_user_id=identity.id,
    )


def doctor_get_printable_prescription(
    db: Session,
    *,
    token: str,
    prescription_id: int,
) -> PrintablePrescriptionView:
    identity = require_role(db, token, Role.MEDICO)
    return get_printable_prescription(
        db,
        prescription_id=prescription_id,
        doctor_user_id=identity.id,
    )


def admin_preview_prescriptions_for_records(
    db: Session,
    *,
    token: str,
    clinical_care_record_ids: list[int],
) -> dict[int, tuple[PrescriptionView, ...]]:
    require_local_admin_preview(db, token)
    return list_prescriptions_for_records(
        db,
        clinical_care_record_ids=clinical_care_record_ids,
    )
