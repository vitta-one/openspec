"""PostgreSQL-specific locking and active-slot integrity tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError,
    create_availability_slot,
    reschedule_consultation,
    schedule_consultation,
)
from vitta_one.models.appointment import Consultation, ConsultationScheduleChange, ProfessionalAvailabilitySlot
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty
from vitta_one.patient_queue.service import create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty

_DATABASE_URL = os.getenv("DATABASE_URL", "")


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


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Scheduling concurrency requires the project PostgreSQL database.",
)
def test_concurrent_reservation_creates_at_most_one_active_consultation() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    suffix = uuid4().hex[:10]
    specialty_id = 0
    professional_id = 0
    slot_id = 0
    patient_ids: list[int] = []
    now = datetime.now(timezone.utc)

    try:
        with Session(engine) as db:
            specialty = create_specialty(db, name=f"Agenda Conc {suffix}")
            specialty_id = specialty.id
            professional = create_professional(
                db,
                name=f"Profissional Conc {suffix}",
                registration_identifier=f"REG-CONC-{suffix}",
                specialty_ids=[specialty.id],
            )
            professional_id = professional.id
            slot = create_availability_slot(
                db,
                professional_id=professional.id,
                starts_at=now + timedelta(days=10),
                now=now,
            )
            slot_id = slot.id
            for position, prefix in enumerate(("123456789", "987654321")):
                patient = create_patient(
                    db,
                    name=f"Paciente Conc {position} {suffix}",
                    cpf=_cpf(prefix),
                )
                patient_ids.append(patient.id)

        def reserve(patient_id: int):
            with Session(engine) as db:
                try:
                    consultation = schedule_consultation(
                        db,
                        patient_id=patient_id,
                        slot_id=slot_id,
                        now=now,
                    )
                    return consultation.id
                except SchedulingConflictError:
                    return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, patient_ids))
        created = [value for value in results if value is not None]
        assert len(created) == 1

        with Session(engine) as db:
            active = db.exec(
                select(Consultation).where(
                    Consultation.availability_slot_id == slot_id,
                    Consultation.status != ConsultationStatus.CANCELADA.value,
                )
            ).all()
            assert len(active) == 1
    finally:
        with Session(engine) as db:
            rows = (
                db.exec(
                    select(Consultation).where(
                        Consultation.availability_slot_id == slot_id
                    )
                ).all()
                if slot_id
                else []
            )
            for row in rows:
                db.delete(row)
            db.commit()

            if slot_id:
                row = db.get(ProfessionalAvailabilitySlot, slot_id)
                if row is not None:
                    db.delete(row)
            db.commit()

            for patient_id in patient_ids:
                row = db.get(Patient, patient_id)
                if row is not None:
                    db.delete(row)
            db.commit()

            if professional_id:
                links = db.exec(
                    select(ProfessionalSpecialty).where(
                        ProfessionalSpecialty.professional_id == professional_id
                    )
                ).all()
                for link in links:
                    db.delete(link)
                db.commit()
                row = db.get(Professional, professional_id)
                if row is not None:
                    db.delete(row)
                db.commit()

            if specialty_id:
                row = db.get(Specialty, specialty_id)
                if row is not None:
                    db.delete(row)
                db.commit()

@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Scheduling concurrency requires the project PostgreSQL database.",
)
def test_concurrent_reschedule_preserves_original_when_destination_is_lost() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    suffix = uuid4().hex[:10]
    specialty_id = 0
    professional_id = 0
    source_slot_id = 0
    destination_slot_id = 0
    patient_ids: list[int] = []
    consultation_id = 0
    now = datetime.now(timezone.utc)

    try:
        with Session(engine) as db:
            specialty = create_specialty(db, name=f"Agenda Move {suffix}")
            specialty_id = specialty.id
            professional = create_professional(
                db,
                name=f"Profissional Move {suffix}",
                registration_identifier=f"REG-MOVE-{suffix}",
                specialty_ids=[specialty.id],
            )
            professional_id = professional.id
            source = create_availability_slot(
                db,
                professional_id=professional.id,
                starts_at=now + timedelta(days=11),
                now=now,
            )
            destination = create_availability_slot(
                db,
                professional_id=professional.id,
                starts_at=now + timedelta(days=12),
                now=now,
            )
            source_slot_id = source.id
            destination_slot_id = destination.id

            for position, prefix in enumerate(("246813579", "135792468")):
                patient = create_patient(
                    db,
                    name=f"Paciente Move {position} {suffix}",
                    cpf=_cpf(prefix),
                )
                patient_ids.append(patient.id)

            consultation = schedule_consultation(
                db,
                patient_id=patient_ids[0],
                slot_id=source_slot_id,
                now=now,
            )
            consultation_id = consultation.id

        def move():
            with Session(engine) as db:
                try:
                    result = reschedule_consultation(
                        db,
                        consultation_id=consultation_id,
                        new_slot_id=destination_slot_id,
                        now=now,
                    )
                    return ("move", result.id)
                except SchedulingConflictError:
                    return ("move-conflict", None)

        def reserve_destination():
            with Session(engine) as db:
                try:
                    result = schedule_consultation(
                        db,
                        patient_id=patient_ids[1],
                        slot_id=destination_slot_id,
                        now=now,
                    )
                    return ("reserve", result.id)
                except SchedulingConflictError:
                    return ("reserve-conflict", None)

        with ThreadPoolExecutor(max_workers=2) as pool:
            move_future = pool.submit(move)
            reserve_future = pool.submit(reserve_destination)
            results = [move_future.result(), reserve_future.result()]

        winners = [kind for kind, value in results if value is not None]
        assert len(winners) == 1

        with Session(engine) as db:
            stored = db.get(Consultation, consultation_id)
            source = db.get(ProfessionalAvailabilitySlot, source_slot_id)
            destination = db.get(ProfessionalAvailabilitySlot, destination_slot_id)
            assert stored is not None
            assert source is not None
            assert destination is not None

            active_destination = db.exec(
                select(Consultation).where(
                    Consultation.availability_slot_id == destination_slot_id,
                    Consultation.status != ConsultationStatus.CANCELADA.value,
                )
            ).all()
            assert len(active_destination) == 1

            if "move" in winners:
                assert stored.availability_slot_id == destination_slot_id
                assert source.status == AvailabilitySlotStatus.AVAILABLE.value
                assert destination.status == AvailabilitySlotStatus.BOOKED.value
            else:
                assert stored.availability_slot_id == source_slot_id
                assert source.status == AvailabilitySlotStatus.BOOKED.value
                assert destination.status == AvailabilitySlotStatus.BOOKED.value
    finally:
        with Session(engine) as db:
            if source_slot_id or destination_slot_id:
                rows = db.exec(
                    select(Consultation).where(
                        Consultation.availability_slot_id.in_(
                            [value for value in (source_slot_id, destination_slot_id) if value]
                        )
                    )
                ).all()
                consultation_ids = [row.id for row in rows if row.id is not None]
                if consultation_ids:
                    schedule_changes = db.exec(
                        select(ConsultationScheduleChange).where(
                            ConsultationScheduleChange.consultation_id.in_(consultation_ids)
                        )
                    ).all()
                    for change in schedule_changes:
                        db.delete(change)
                    db.flush()
                for row in rows:
                    db.delete(row)
                db.commit()

            for slot_id in (source_slot_id, destination_slot_id):
                if slot_id:
                    row = db.get(ProfessionalAvailabilitySlot, slot_id)
                    if row is not None:
                        db.delete(row)
            db.commit()

            for patient_id in patient_ids:
                row = db.get(Patient, patient_id)
                if row is not None:
                    db.delete(row)
            db.commit()

            if professional_id:
                links = db.exec(
                    select(ProfessionalSpecialty).where(
                        ProfessionalSpecialty.professional_id == professional_id
                    )
                ).all()
                for link in links:
                    db.delete(link)
                db.commit()
                row = db.get(Professional, professional_id)
                if row is not None:
                    db.delete(row)
                db.commit()

            if specialty_id:
                row = db.get(Specialty, specialty_id)
                if row is not None:
                    db.delete(row)
                db.commit()

