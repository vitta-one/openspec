"""PostgreSQL concurrency tests for the scheduled consultation care bridge."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

from vitta_one.appointment_scheduling.domain import ConsultationStatus
from vitta_one.appointment_scheduling.service import (
    create_availability_slot,
    schedule_consultation,
)
from vitta_one.auth.roles import Role
from vitta_one.consultation_care.service import (
    CareLifecycleConflictError,
    CareLifecycleTransitionError,
    confirm_arrival,
)
from vitta_one.clinical_care.service import save_active_record
from vitta_one.models.appointment import Consultation
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import QueueEntry
from vitta_one.patient_queue.service import (
    DoctorAlreadyAttendingError,
    QueueEmptyError,
    claim_next_patient,
    create_patient,
)
from vitta_one.professional_directory.service import (
    create_professional,
    create_specialty,
)

_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _cpf(prefix: str) -> str:
    digits = [int(char) for char in prefix]
    for weights in (range(10, 1, -1), range(11, 1, -1)):
        total = sum(digit * weight for digit, weight in zip(digits, weights))
        check = (total * 10) % 11
        digits.append(0 if check == 10 else check)
    return "".join(str(digit) for digit in digits)


def _seed(engine, patient_prefix: str):
    suffix = uuid4().hex[:10]
    base = datetime.now(timezone.utc)
    with Session(engine) as db:
        doctor = User(
            email=f"care-{suffix}@example.invalid",
            password_hash="test-only-hash",
            role=Role.MEDICO.value,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        specialty = create_specialty(db, name=f"Care {suffix}")
        professional = create_professional(
            db,
            name=f"Profissional {suffix}",
            registration_identifier=f"CARE-{suffix}",
            specialty_ids=[specialty.id],
            user_id=doctor.id,
        )
        patient = create_patient(
            db,
            name=f"Paciente {suffix}",
            cpf=_cpf(patient_prefix),
        )
        slot = create_availability_slot(
            db,
            professional_id=professional.id,
            starts_at=base + timedelta(days=3),
            now=base,
        )
        consultation = schedule_consultation(
            db,
            patient_id=patient.id,
            slot_id=slot.id,
            now=base,
        )
        return doctor.id, consultation.id, base


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Lifecycle concurrency requires PostgreSQL.",
)
def test_concurrent_arrival_creates_one_linked_queue_entry() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, consultation_id, base = _seed(engine, "123456789")

    def arrive():
        with Session(engine) as db:
            try:
                return confirm_arrival(
                    db,
                    consultation_id=consultation_id,
                    symptoms="Relato concorrente",
                    priority="AMARELO",
                    now=base + timedelta(hours=1),
                ).id
            except (CareLifecycleConflictError, CareLifecycleTransitionError):
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: arrive(), range(2)))

    assert len([value for value in results if value is not None]) == 1
    with Session(engine) as db:
        entries = db.exec(
            select(QueueEntry).where(QueueEntry.consultation_id == consultation_id)
        ).all()
        consultation = db.get(Consultation, consultation_id)
        assert len(entries) == 1
        assert consultation is not None
        assert consultation.status == ConsultationStatus.CONFIRMADA.value
        assert consultation.confirmed_at is not None
        assert doctor_id is not None


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Lifecycle concurrency requires PostgreSQL.",
)
def test_concurrent_claim_keeps_queue_and_consultation_in_sync() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, consultation_id, base = _seed(engine, "987654321")
    with Session(engine) as db:
        entry = confirm_arrival(
            db,
            consultation_id=consultation_id,
            symptoms="Relato para chamada",
            priority="VERMELHO",
            now=base + timedelta(hours=1),
        )
        entry_id = entry.id

    def claim():
        with Session(engine) as db:
            try:
                return claim_next_patient(
                    db,
                    doctor_user_id=doctor_id,
                    now=base + timedelta(hours=2),
                ).id
            except (DoctorAlreadyAttendingError, QueueEmptyError):
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))

    assert len([value for value in results if value is not None]) == 1
    with Session(engine) as db:
        entry = db.get(QueueEntry, entry_id)
        consultation = db.get(Consultation, consultation_id)
        assert entry is not None and consultation is not None
        assert entry.status == "EM_ATENDIMENTO"
        assert consultation.status == ConsultationStatus.EM_ANDAMENTO.value
        assert consultation.started_at == entry.called_at
        records = db.exec(
            select(ClinicalCareRecord).where(
                ClinicalCareRecord.consultation_id == consultation_id
            )
        ).all()
        assert len(records) == 1

@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Clinical record locking requires PostgreSQL.",
)
def test_concurrent_clinical_saves_are_serialized_without_mixed_payload() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, consultation_id, base = _seed(engine, "246813579")
    with Session(engine) as db:
        entry = confirm_arrival(
            db,
            consultation_id=consultation_id,
            symptoms="Relato para save concorrente",
            priority="AMARELO",
            now=base + timedelta(hours=1),
        )
        entry_id = entry.id
        claim_next_patient(
            db,
            doctor_user_id=doctor_id,
            now=base + timedelta(hours=2),
        )

    payloads = [
        {
            "chief_complaint": "Queixa A",
            "anamnesis": "Anamnese A",
            "diagnosis": "Diagnóstico A",
            "conduct_notes": "Conduta A",
        },
        {
            "chief_complaint": "Queixa B",
            "anamnesis": "Anamnese B",
            "diagnosis": "Diagnóstico B",
            "conduct_notes": "Conduta B",
        },
    ]

    def save(payload):
        with Session(engine) as db:
            item = save_active_record(
                db,
                entry_id=entry_id,
                doctor_user_id=doctor_id,
                **payload,
            )
            return (
                item.chief_complaint,
                item.anamnesis,
                item.diagnosis,
                item.conduct_notes,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, payloads))

    assert len(results) == 2
    allowed = {
        ("Queixa A", "Anamnese A", "Diagnóstico A", "Conduta A"),
        ("Queixa B", "Anamnese B", "Diagnóstico B", "Conduta B"),
    }
    with Session(engine) as db:
        record = db.exec(
            select(ClinicalCareRecord).where(
                ClinicalCareRecord.consultation_id == consultation_id
            )
        ).one()
        stored = (
            record.chief_complaint,
            record.anamnesis,
            record.diagnosis,
            record.conduct_notes,
        )
        assert stored in allowed

