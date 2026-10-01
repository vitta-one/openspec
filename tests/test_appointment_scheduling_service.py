"""Business-rule coverage for appointment scheduling."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError,
    SchedulingTransitionError,
    SchedulingValidationError,
    cancel_consultation,
    create_availability_slot,
    get_agenda,
    reschedule_consultation,
    schedule_consultation,
    set_availability_slot_active,
)
from vitta_one.appointment_scheduling.settings import ClinicTimezoneConfigurationError, clinic_timezone_name
from vitta_one.appointment_scheduling.temporal import clinic_date_range_to_utc, format_clinic_datetime, parse_clinic_datetime_local
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.patient_queue.service import create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty, set_professional_active


def _cpf(prefix: str) -> str:
    digits = [int(char) for char in prefix]
    first_total = sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1)))
    first = (first_total * 10) % 11
    if first == 10:
        first = 0
    digits.append(first)
    second_total = sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1)))
    second = (second_total * 10) % 11
    if second == 10:
        second = 0
    digits.append(second)
    return "".join(str(digit) for digit in digits)


@pytest.fixture(autouse=True)
def clinic_timezone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _professional(db: Session, identifier: str = "REG-1"):
    specialty = create_specialty(db, name=f"Especialidade {identifier}")
    return create_professional(
        db,
        name=f"Profissional {identifier}",
        registration_identifier=identifier,
        specialty_ids=[specialty.id],
    )


def test_timezone_is_explicit_and_converts_local_to_utc(monkeypatch: pytest.MonkeyPatch) -> None:
    assert clinic_timezone_name() == "America/Sao_Paulo"
    instant = parse_clinic_datetime_local("2026-10-01T10:30")
    assert instant == datetime(2026, 10, 1, 13, 30, tzinfo=timezone.utc)
    assert format_clinic_datetime(instant) == "01/10/2026 às 10:30"

    start, end = clinic_date_range_to_utc("2026-10-01", "2026-10-01")
    assert start == datetime(2026, 10, 1, 3, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 2, 3, 0, tzinfo=timezone.utc)

    monkeypatch.delenv("VITTA_ONE_CLINIC_TIMEZONE")
    with pytest.raises(ClinicTimezoneConfigurationError):
        parse_clinic_datetime_local("2026-10-01T10:30")

    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "Timezone/Invalido")
    with pytest.raises(ClinicTimezoneConfigurationError):
        clinic_timezone_name()


def test_slot_create_duplicate_past_deactivate_and_reactivate(db: Session) -> None:
    professional = _professional(db)
    now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    future = now + timedelta(days=1)
    slot = create_availability_slot(db, professional_id=professional.id, starts_at=future, now=now)
    assert slot.status == AvailabilitySlotStatus.AVAILABLE.value

    with pytest.raises(SchedulingConflictError):
        create_availability_slot(db, professional_id=professional.id, starts_at=future, now=now)
    with pytest.raises(SchedulingValidationError):
        create_availability_slot(db, professional_id=professional.id, starts_at=now - timedelta(minutes=1), now=now)

    set_availability_slot_active(db, slot_id=slot.id, is_active=False, now=now)
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.INACTIVE.value
    set_availability_slot_active(db, slot_id=slot.id, is_active=True, now=now)
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.AVAILABLE.value


def test_schedule_cancel_and_reuse_slot_preserves_history(db: Session) -> None:
    professional = _professional(db)
    first_patient = create_patient(db, name="Paciente Um", cpf=_cpf("123456789"))
    second_patient = create_patient(db, name="Paciente Dois", cpf=_cpf("987654321"))
    now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    slot = create_availability_slot(db, professional_id=professional.id, starts_at=now + timedelta(days=1), now=now)

    with pytest.raises(SchedulingValidationError):
        schedule_consultation(db, patient_id=999999, slot_id=slot.id, now=now)
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.AVAILABLE.value

    consultation = schedule_consultation(db, patient_id=first_patient.id, slot_id=slot.id, now=now)
    assert consultation.status == ConsultationStatus.AGENDADA.value
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.BOOKED.value

    with pytest.raises(SchedulingConflictError):
        schedule_consultation(db, patient_id=second_patient.id, slot_id=slot.id, now=now)

    with pytest.raises(SchedulingTransitionError):
        set_availability_slot_active(db, slot_id=slot.id, is_active=False, now=now)

    cancelled = cancel_consultation(db, consultation_id=consultation.id, now=now + timedelta(hours=1))
    first_cancelled_at = cancelled.cancelled_at
    assert cancelled.status == ConsultationStatus.CANCELADA.value
    assert db.get(ProfessionalAvailabilitySlot, slot.id).status == AvailabilitySlotStatus.AVAILABLE.value

    with pytest.raises(SchedulingTransitionError):
        cancel_consultation(db, consultation_id=consultation.id, now=now + timedelta(hours=2))
    assert db.get(Consultation, consultation.id).cancelled_at == first_cancelled_at

    second = schedule_consultation(db, patient_id=second_patient.id, slot_id=slot.id, now=now + timedelta(hours=2))
    assert second.id != consultation.id
    snapshot = get_agenda(db)
    assert len(snapshot.consultations) == 2


def test_reschedule_can_change_professional(db: Session) -> None:
    first_professional = _professional(db, "REG-A")
    second_professional = _professional(db, "REG-B")
    patient = create_patient(db, name="Paciente Agenda", cpf=_cpf("246813579"))
    now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    first_slot = create_availability_slot(db, professional_id=first_professional.id, starts_at=now + timedelta(days=1), now=now)
    second_slot = create_availability_slot(db, professional_id=second_professional.id, starts_at=now + timedelta(days=2), now=now)
    consultation = schedule_consultation(db, patient_id=patient.id, slot_id=first_slot.id, now=now)

    moved = reschedule_consultation(db, consultation_id=consultation.id, new_slot_id=second_slot.id, now=now)
    assert moved.patient_id == patient.id
    assert moved.professional_id == second_professional.id
    assert db.get(ProfessionalAvailabilitySlot, first_slot.id).status == AvailabilitySlotStatus.AVAILABLE.value
    assert db.get(ProfessionalAvailabilitySlot, second_slot.id).status == AvailabilitySlotStatus.BOOKED.value


def test_inactive_professional_blocks_new_reservation_and_later_states_are_untouched(db: Session) -> None:
    professional = _professional(db)
    patient = create_patient(db, name="Paciente Protegido", cpf=_cpf("135792468"))
    now = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    slot = create_availability_slot(db, professional_id=professional.id, starts_at=now + timedelta(days=1), now=now)
    set_professional_active(db, professional_id=professional.id, is_active=False)
    with pytest.raises(SchedulingValidationError):
        schedule_consultation(db, patient_id=patient.id, slot_id=slot.id, now=now)

    set_professional_active(db, professional_id=professional.id, is_active=True)
    consultation = schedule_consultation(db, patient_id=patient.id, slot_id=slot.id, now=now)
    consultation.status = ConsultationStatus.CONFIRMADA.value
    db.add(consultation)
    db.commit()

    other_slot = create_availability_slot(db, professional_id=professional.id, starts_at=now + timedelta(days=2), now=now)
    with pytest.raises(SchedulingTransitionError):
        reschedule_consultation(db, consultation_id=consultation.id, new_slot_id=other_slot.id, now=now)
    with pytest.raises(SchedulingTransitionError):
        cancel_consultation(db, consultation_id=consultation.id, now=now)
    assert db.get(Consultation, consultation.id).status == ConsultationStatus.CONFIRMADA.value
