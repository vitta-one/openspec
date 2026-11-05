"""PostgreSQL concurrency coverage for atomic queue claims."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.service import (
    DoctorAlreadyAttendingError,
    QueueEmptyError,
    QueueItem,
    QueueValidationError,
    claim_next_patient,
    create_patient,
    create_queue_entry,
)

def _random_cpf() -> str:
    digits = [int(x) for x in f"{uuid4().int % 1_000_000_000:09d}"]
    for weights in (range(10, 1, -1), range(11, 1, -1)):
        digit = (sum(n * w for n, w in zip(digits, weights)) * 10) % 11
        digits.append(0 if digit == 10 else digit)
    return "".join(str(x) for x in digits)


_DATABASE_URL = os.getenv("DATABASE_URL", "")


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Concurrency locking requires the project PostgreSQL database.",
)
def test_two_doctors_cannot_claim_the_same_waiting_entry() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)

    doctor_ids: list[int] = []
    patient_id = 0
    entry_id = 0

    try:
        with Session(engine) as db:
            for position in (1, 2):
                doctor = User(
                    email=f"queue-concurrency-{position}-{uuid4().hex}@example.invalid",
                    password_hash="test-only-hash",
                    role="MEDICO",
                )
                db.add(doctor)
                db.commit()
                db.refresh(doctor)
                assert doctor.id is not None
                doctor_ids.append(doctor.id)

            patient = create_patient(
                db,
                name="Paciente Concorrência",
                cpf=_random_cpf(),
            )
            assert patient.id is not None
            patient_id = patient.id

            entry = create_queue_entry(
                db,
                patient_id=patient.id,
                symptoms="Relato para teste concorrente",
                priority="VERMELHO",
            )
            assert entry.id is not None
            entry_id = entry.id

        def claim(doctor_id: int) -> QueueItem | None:
            with Session(engine) as db:
                try:
                    return claim_next_patient(db, doctor_user_id=doctor_id)
                except QueueEmptyError:
                    return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(claim, doctor_ids))

        claimed = [item for item in results if item is not None]
        assert len(claimed) == 1
        assert claimed[0].id == entry_id
        assert claimed[0].doctor_user_id in doctor_ids

        with Session(engine) as db:
            stored = db.get(QueueEntry, entry_id)
            assert stored is not None
            assert stored.doctor_user_id == claimed[0].doctor_user_id
            assert stored.status == "EM_ATENDIMENTO"
    finally:
        with Session(engine) as db:
            if entry_id:
                record = db.exec(
                    select(ClinicalCareRecord).where(
                        ClinicalCareRecord.queue_entry_id == entry_id
                    )
                ).first()
                if record is not None:
                    db.delete(record)
                    db.flush()
                row = db.get(QueueEntry, entry_id)
                if row is not None:
                    db.delete(row)
                    db.commit()
            if patient_id:
                row = db.get(Patient, patient_id)
                if row is not None:
                    db.delete(row)
                    db.commit()
            for doctor_id in doctor_ids:
                row = db.get(User, doctor_id)
                if row is not None:
                    db.delete(row)
                    db.commit()


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Concurrency locking requires the project PostgreSQL database.",
)
def test_same_doctor_cannot_claim_two_patients_concurrently() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)

    doctor_id = 0
    patient_ids: list[int] = []
    entry_ids: list[int] = []

    try:
        with Session(engine) as db:
            doctor = User(
                email=f"queue-same-doctor-{uuid4().hex}@example.invalid",
                password_hash="test-only-hash",
                role="MEDICO",
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            assert doctor.id is not None
            doctor_id = doctor.id

            for name, cpf in (
                ("Paciente Um", _random_cpf()),
                ("Paciente Dois", _random_cpf()),
            ):
                patient = create_patient(db, name=name, cpf=cpf)
                assert patient.id is not None
                patient_ids.append(patient.id)
                entry = create_queue_entry(
                    db,
                    patient_id=patient.id,
                    symptoms="Relato concorrente",
                    priority="AMARELO",
                )
                assert entry.id is not None
                entry_ids.append(entry.id)

        def claim() -> QueueItem | str:
            with Session(engine) as db:
                try:
                    return claim_next_patient(db, doctor_user_id=doctor_id)
                except DoctorAlreadyAttendingError:
                    return "already-attending"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: claim(), range(2)))

        claimed = [item for item in results if isinstance(item, QueueItem)]
        blocked = [item for item in results if item == "already-attending"]
        assert len(claimed) == 1
        assert len(blocked) == 1

        with Session(engine) as db:
            entries = [db.get(QueueEntry, entry_id) for entry_id in entry_ids]
            assert sum(
                entry is not None and entry.status == "EM_ATENDIMENTO"
                for entry in entries
            ) == 1
            assert sum(
                entry is not None and entry.status == "AGUARDANDO"
                for entry in entries
            ) == 1
    finally:
        with Session(engine) as db:
            for entry_id in entry_ids:
                record = db.exec(
                    select(ClinicalCareRecord).where(
                        ClinicalCareRecord.queue_entry_id == entry_id
                    )
                ).first()
                if record is not None:
                    db.delete(record)
            db.flush()
            for entry_id in entry_ids:
                row = db.get(QueueEntry, entry_id)
                if row is not None:
                    db.delete(row)
            db.commit()
            for patient_id in patient_ids:
                row = db.get(Patient, patient_id)
                if row is not None:
                    db.delete(row)
            db.commit()
            if doctor_id:
                row = db.get(User, doctor_id)
                if row is not None:
                    db.delete(row)
            db.commit()



@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Patient arrival row locking requires PostgreSQL.",
)
def test_concurrent_walk_in_submissions_create_one_active_entry() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    patient_id = 0
    try:
        with Session(engine) as db:
            patient = create_patient(
                db, name="Chegada concorrente", cpf=_random_cpf()
            )
            assert patient.id is not None
            patient_id = patient.id

        def arrive() -> str:
            with Session(engine) as db:
                try:
                    create_queue_entry(
                        db, patient_id=patient_id,
                        symptoms="Tentativa concorrente",
                        priority="AMARELO",
                    )
                    return "created"
                except QueueValidationError:
                    return "already-active"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: arrive(), range(2)))

        assert sorted(results) == ["already-active", "created"]
        with Session(engine) as db:
            active = db.exec(
                select(QueueEntry).where(
                    QueueEntry.patient_id == patient_id,
                    QueueEntry.status == "AGUARDANDO",
                )
            ).all()
            assert len(active) == 1
    finally:
        with Session(engine) as db:
            for entry in db.exec(
                select(QueueEntry).where(QueueEntry.patient_id == patient_id)
            ).all():
                db.delete(entry)
            db.commit()
            if patient_id:
                patient = db.get(Patient, patient_id)
                if patient is not None:
                    db.delete(patient)
                    db.commit()
