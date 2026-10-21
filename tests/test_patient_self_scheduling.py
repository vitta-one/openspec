"""End-to-end domain/RBAC tests for patient-controlled appointment scheduling."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.appointment_scheduling.application import (
    doctor_get_my_agenda,
    patient_get_booking_options,
    patient_get_my_agenda,
    patient_schedule_own_consultation,
    reception_get_agenda,
    reception_schedule_consultation,
)
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError, SchedulingValidationError,
)
from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.auth.service import create_session
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty
from vitta_one.patient_portal.booking import (
    list_patient_doctors, list_patient_slots, list_patient_specialties,
)


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def user(db, role, email):
    u = User(email=email, role=role.value, password_hash=hash_password("synthetic-test-only"))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u, create_session(db, user_id=u.id, ttl=timedelta(hours=1))


def seed(db):
    owner, patient_token = user(db, Role.PACIENTE, "booker@example.invalid")
    other, other_token = user(db, Role.PACIENTE, "other@example.invalid")
    doctor_user, doctor_token = user(db, Role.MEDICO, "doctor@example.invalid")
    _, receptionist_token = user(db, Role.RECEPCIONISTA, "reception@example.invalid")
    p = Patient(name="Paciente de QA", cpf="52998224725", user_id=owner.id)
    p_other = Patient(name="Outro paciente", cpf="11144477735", user_id=other.id)
    specialty = Specialty(name="Clínica Geral", normalized_name="clinica geral", is_active=True)
    unavailable_specialty = Specialty(name="Inativa", normalized_name="inativa", is_active=False)
    active = Professional(
        name="Dra. Teste", registration_identifier="CRM-QA-BOOKING",
        is_active=True, user_id=doctor_user.id,
    )
    inactive = Professional(
        name="Dr. Inativo", registration_identifier="CRM-QA-INACTIVE", is_active=False,
    )
    db.add_all([p, p_other, specialty, unavailable_specialty, active, inactive])
    db.commit()
    for row in [p, p_other, specialty, unavailable_specialty, active, inactive]:
        db.refresh(row)
    db.add_all([
        ProfessionalSpecialty(professional_id=active.id, specialty_id=specialty.id),
        ProfessionalSpecialty(professional_id=active.id, specialty_id=unavailable_specialty.id),
        ProfessionalSpecialty(professional_id=inactive.id, specialty_id=specialty.id),
    ])
    starts = datetime(2099, 8, 11, 13, tzinfo=timezone.utc)
    slot = ProfessionalAvailabilitySlot(
        professional_id=active.id, starts_at=starts, status=AvailabilitySlotStatus.AVAILABLE.value
    )
    second = ProfessionalAvailabilitySlot(
        professional_id=active.id,
        starts_at=starts + timedelta(days=1),
        status=AvailabilitySlotStatus.AVAILABLE.value
    )
    db.add_all([slot, second])
    db.commit()
    db.refresh(slot)
    db.refresh(second)
    return {
        "patient": p, "other": p_other, "doctor": active, "specialty": specialty,
        "slot": slot, "second": second,
        "patient_token": patient_token, "other_token": other_token,
        "doctor_token": doctor_token, "reception_token": receptionist_token,
        "starts": starts,
    }


def test_patient_can_choose_specialty_doctor_and_own_slot(db):
    x = seed(db)
    specialties, doctors, _ = patient_get_booking_options(
        db, token=x["patient_token"], specialty_id=x["specialty"].id
    )
    assert [item.name for item in specialties] == ["Clínica Geral"]
    assert [item.id for item in doctors] == [x["doctor"].id]
    slots = list_patient_slots(
        db, specialty_id=x["specialty"].id,
        professional_id=x["doctor"].id, now=datetime(2099, 8, 10, tzinfo=timezone.utc),
    )
    assert [item.id for item in slots] == [x["slot"].id, x["second"].id]
    created = patient_schedule_own_consultation(
        db, token=x["patient_token"], specialty_id=x["specialty"].id,
        professional_id=x["doctor"].id, slot_id=x["slot"].id
    )
    assert created.patient_id == x["patient"].id
    assert created.professional_id == x["doctor"].id
    assert created.status == ConsultationStatus.AGENDADA.value
    assert db.get(ProfessionalAvailabilitySlot, x["slot"].id).status == "BOOKED"
    _, patient_appointments = patient_get_my_agenda(
        db, token=x["patient_token"], start_date="2099-08-01", end_date="2099-08-31"
    )
    _, doctor_appointments = doctor_get_my_agenda(
        db, token=x["doctor_token"], start_date="2099-08-01", end_date="2099-08-31"
    )
    reception = reception_get_agenda(
        db, token=x["reception_token"], start_date="2099-08-01", end_date="2099-08-31"
    )
    assert [item.id for item in patient_appointments] == [created.id]
    assert [item.id for item in doctor_appointments] == [created.id]
    assert [item.id for item in reception.consultations] == [created.id]
    assert patient_get_my_agenda(
        db, token=x["other_token"], start_date="2099-08-01", end_date="2099-08-31"
    )[1] == ()


def test_booking_rejects_forged_identity_specialty_doctor_and_slot(db):
    x = seed(db)
    with pytest.raises(RoleForbiddenError):
        patient_schedule_own_consultation(
            db, token=x["reception_token"], specialty_id=x["specialty"].id,
            professional_id=x["doctor"].id, slot_id=x["slot"].id,
        )
    with pytest.raises(AuthenticationRequiredError):
        patient_get_booking_options(db, token="")
    with pytest.raises(SchedulingValidationError):
        patient_schedule_own_consultation(
            db, token=x["patient_token"], specialty_id=9999,
            professional_id=x["doctor"].id, slot_id=x["slot"].id,
        )
    with pytest.raises(SchedulingValidationError):
        patient_schedule_own_consultation(
            db, token=x["patient_token"], specialty_id=x["specialty"].id,
            professional_id=9999, slot_id=x["slot"].id,
        )
    assert db.exec(select(Consultation)).all() == []


def test_two_patients_cannot_take_same_slot(db):
    x = seed(db)
    patient_schedule_own_consultation(
        db, token=x["patient_token"], specialty_id=x["specialty"].id,
        professional_id=x["doctor"].id, slot_id=x["slot"].id,
    )
    with pytest.raises(SchedulingConflictError):
        patient_schedule_own_consultation(
            db, token=x["other_token"], specialty_id=x["specialty"].id,
            professional_id=x["doctor"].id, slot_id=x["slot"].id,
        )
    assert len(db.exec(select(Consultation)).all()) == 1


def test_reception_and_patient_share_same_reservation_rules(db):
    x = seed(db)
    created = reception_schedule_consultation(
        db, token=x["reception_token"], patient_id=x["patient"].id, slot_id=x["slot"].id,
    )
    with pytest.raises(SchedulingConflictError):
        patient_schedule_own_consultation(
            db, token=x["patient_token"], specialty_id=x["specialty"].id,
            professional_id=x["doctor"].id, slot_id=x["slot"].id,
        )
    assert len(db.exec(select(Consultation)).all()) == 1
    assert created.patient_id == x["patient"].id


def test_patient_without_linked_account_is_rejected(db):
    _owner, token = user(db, Role.PACIENTE, "unlinked@example.invalid")
    with pytest.raises(SchedulingValidationError, match="vinculado"):
        patient_schedule_own_consultation(
            db, token=token, specialty_id=1, professional_id=1, slot_id=1,
        )


def test_same_patient_cannot_book_two_doctors_at_same_instant(db):
    x = seed(db)
    second_doctor = Professional(
        name="Dr. Outro", registration_identifier="CRM-QA-SECOND", is_active=True
    )
    db.add(second_doctor)
    db.commit()
    db.refresh(second_doctor)
    db.add(ProfessionalSpecialty(
        professional_id=second_doctor.id, specialty_id=x["specialty"].id
    ))
    other_slot = ProfessionalAvailabilitySlot(
        professional_id=second_doctor.id, starts_at=x["starts"],
        status=AvailabilitySlotStatus.AVAILABLE.value,
    )
    db.add(other_slot)
    db.commit()
    db.refresh(other_slot)

    first = patient_schedule_own_consultation(
        db, token=x["patient_token"], specialty_id=x["specialty"].id,
        professional_id=x["doctor"].id, slot_id=x["slot"].id,
    )
    with pytest.raises(SchedulingConflictError, match="já possui"):
        patient_schedule_own_consultation(
            db, token=x["patient_token"], specialty_id=x["specialty"].id,
            professional_id=second_doctor.id, slot_id=other_slot.id,
        )

    assert db.get(ProfessionalAvailabilitySlot, other_slot.id).status == "AVAILABLE"
    assert db.exec(select(Consultation)).one().id == first.id


def test_patient_catalog_hides_inactive_specialties_and_doctors(db):
    x = seed(db)
    assert [s.name for s in list_patient_specialties(db)] == ["Clínica Geral"]
    assert [d.name for d in list_patient_doctors(
        db, specialty_id=x["specialty"].id
    )] == ["Dra. Teste"]
    assert list_patient_doctors(db, specialty_id=9999) == ()
    assert list_patient_slots(
        db, specialty_id=9999, professional_id=x["doctor"].id
    ) == ()
