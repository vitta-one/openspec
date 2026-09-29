"""PostgreSQL concurrency coverage for atomic queue claims."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine

from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.patient_queue.service import (
    QueueEmptyError,
    QueueItem,
    claim_next_patient,
    create_patient,
    create_queue_entry,
)

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
                cpf="52998224725",
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
