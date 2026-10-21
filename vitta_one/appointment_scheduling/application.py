"""Authorized application operations for appointment scheduling."""

from sqlmodel import Session, select

from vitta_one.appointment_scheduling.service import (
    AgendaSnapshot,
    AvailabilitySlotItem,
    ProfessionalOption,
    SchedulingValidationError,
    SchedulingNotFoundError,
    cancel_consultation,
    create_availability_slot,
    get_agenda,
    list_active_professionals,
    list_availability_slots,
    list_consultations,
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
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional


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


def reception_get_consultation_by_id(
    db: Session, *, token: str, consultation_id: int
):
    """Revalidate one chosen consultation under Reception RBAC, independent of filters."""
    require_role(db, token, Role.RECEPCIONISTA)
    items = list_consultations(db, consultation_id=consultation_id)
    if not items:
        raise SchedulingNotFoundError("Esta consulta não está mais disponível.")
    return items[0]


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
    identity = require_role(db, token, Role.RECEPCIONISTA)
    return reschedule_consultation(
        db,
        consultation_id=consultation_id,
        new_slot_id=new_slot_id,
        changed_by_user_id=identity.id,
    )


def doctor_get_my_agenda(
    db: Session,
    *,
    token: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[Professional, tuple]:
    """Return an authenticated doctor's own schedule, never a client-selected one."""
    identity = require_role(db, token, Role.MEDICO)
    professional = db.exec(
        select(Professional).where(Professional.user_id == identity.id)
    ).first()
    if professional is None or not professional.is_active or professional.id is None:
        raise SchedulingValidationError(
            "Sua conta ainda não está associada a um profissional ativo."
        )
    start_at, end_at = clinic_date_range_to_utc(start_date, end_date)
    return professional, tuple(
        list_consultations(
            db,
            professional_id=professional.id,
            start_at=start_at,
            end_at=end_at,
        )
    )


def patient_get_booking_options(
    db: Session, *, token: str, specialty_id: int | None = None,
    professional_id: int | None = None,
):
    """Expose only the public catalog and bookable slots to authenticated patients."""
    from vitta_one.patient_portal.booking import (
        list_patient_doctors, list_patient_slots, list_patient_specialties,
    )

    require_role(db, token, Role.PACIENTE)
    specialties = list_patient_specialties(db)
    doctors = (
        list_patient_doctors(db, specialty_id=specialty_id)
        if specialty_id is not None else ()
    )
    slots = (
        list_patient_slots(db, specialty_id=specialty_id, professional_id=professional_id)
        if specialty_id is not None and professional_id is not None else ()
    )
    return specialties, doctors, slots


def patient_schedule_own_consultation(
    db: Session, *, token: str, specialty_id: int,
    professional_id: int, slot_id: int,
) -> Consultation:
    """Schedule for the patient bound to the session, not a client-supplied ID."""
    from vitta_one.patient_portal.booking import validate_patient_booking_selection

    identity = require_role(db, token, Role.PACIENTE)
    patient = db.exec(
        select(Patient).where(Patient.user_id == identity.id)
    ).first()
    if patient is None or patient.id is None:
        raise SchedulingValidationError(
            "Seu cadastro não está vinculado a esta conta. Contate a recepção."
        )
    validate_patient_booking_selection(
        db, specialty_id=specialty_id,
        professional_id=professional_id, slot_id=slot_id,
    )
    return schedule_consultation(db, patient_id=patient.id, slot_id=slot_id)


def patient_get_my_agenda(
    db: Session,
    *,
    token: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[Patient, tuple]:
    """Return a patient's own schedule by resolving its link from the session."""
    identity = require_role(db, token, Role.PACIENTE)
    patient = db.exec(select(Patient).where(Patient.user_id == identity.id)).first()
    if patient is None or patient.id is None:
        raise SchedulingValidationError(
            "O cadastro do paciente não está disponível para esta conta."
        )
    start_at, end_at = clinic_date_range_to_utc(start_date, end_date)
    rows = list_consultations(
        db, patient_id=patient.id, start_at=start_at, end_at=end_at
    )
    return patient, tuple(rows)


def doctor_list_my_patients(db: Session, *, token: str) -> tuple[Professional, tuple]:
    """List patients derived only from the authenticated doctor's consultations."""
    professional, consultations = doctor_get_my_agenda(db, token=token)
    seen: set[int] = set()
    result = []
    for item in consultations:
        if item.patient_id not in seen:
            seen.add(item.patient_id)
            result.append((item.patient_id, item.patient_name, item.scheduled_at))
    return professional, tuple(result)


def reception_cancel_consultation(
    db: Session,
    *,
    token: str,
    consultation_id: int,
) -> Consultation:
    require_role(db, token, Role.RECEPCIONISTA)
    return cancel_consultation(db, consultation_id=consultation_id)
