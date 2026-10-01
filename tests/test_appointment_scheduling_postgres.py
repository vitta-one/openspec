"""PostgreSQL-specific locking and active-slot integrity tests."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    SchedulingConflictError,
    create_availability_slot,
    schedule_consultation,
)
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
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
