"""Authorized application operations for appointment scheduling."""

from sqlmodel import Session

from vitta_one.appointment_scheduling.service import (
    AgendaSnapshot,
    AvailabilitySlotItem,
    ProfessionalOption,
    cancel_consultation,
    create_availability_slot,
    get_agenda,
    list_active_professionals,
    list_availability_slots,
    reschedule_consultation,
    schedule_consultation,
    set_availability_slot_active,
)
from vitta_one.appointment_scheduling.temporal import (
    clinic_date_range_to_utc,
    parse_clinic_datetime_local,
)
from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot


def admin_list_active_professionals(db: Session, *, token: str) -> list[ProfessionalOption]:
    require_role(db, token, Role.ADMINISTRADOR)
    return list_active_professionals(db)


def admin_create_availability_slot(
    db: Session,
    *,
    token: str,
    professional_id: int,
    starts_at_local: str,
) -> ProfessionalAvailabilitySlot:
    require_role(db, token, Role.ADMINISTRADOR)
    return create_availability_slot(
        db,
        professional_id=professional_id,
        starts_at=parse_clinic_datetime_local(starts_at_local),
    )


def admin_list_availability_slots(
    db: Session,
    *,
    token: str,
    professional_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[AvailabilitySlotItem]:
    require_role(db, token, Role.ADMINISTRADOR)
    start_at, end_at = clinic_date_range_to_utc(start_date, end_date)
    return list_availability_slots(
        db,
        professional_id=professional_id,
        start_at=start_at,
        end_at=end_at,
    )


def admin_set_availability_slot_active(
    db: Session,
    *,
    token: str,
    slot_id: int,
    is_active: bool,
) -> ProfessionalAvailabilitySlot:
    require_role(db, token, Role.ADMINISTRADOR)
    return set_availability_slot_active(db, slot_id=slot_id, is_active=is_active)


def reception_list_active_professionals(db: Session, *, token: str) -> list[ProfessionalOption]:
    require_role(db, token, Role.RECEPCIONISTA)
    return list_active_professionals(db)


def reception_get_agenda(
    db: Session,
    *,
    token: str,
    professional_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> AgendaSnapshot:
    require_role(db, token, Role.RECEPCIONISTA)
    start_at, end_at = clinic_date_range_to_utc(start_date, end_date)
    return get_agenda(
        db,
        professional_id=professional_id,
        start_at=start_at,
        end_at=end_at,
    )


def reception_schedule_consultation(
    db: Session,
    *,
    token: str,
    patient_id: int,
    slot_id: int,
) -> Consultation:
    require_role(db, token, Role.RECEPCIONISTA)
    return schedule_consultation(db, patient_id=patient_id, slot_id=slot_id)


def reception_reschedule_consultation(
    db: Session,
    *,
    token: str,
    consultation_id: int,
    new_slot_id: int,
) -> Consultation:
    require_role(db, token, Role.RECEPCIONISTA)
    return reschedule_consultation(
        db,
        consultation_id=consultation_id,
        new_slot_id=new_slot_id,
    )


def reception_cancel_consultation(
    db: Session,
    *,
    token: str,
    consultation_id: int,
) -> Consultation:
    require_role(db, token, Role.RECEPCIONISTA)
    return cancel_consultation(db, consultation_id=consultation_id)
