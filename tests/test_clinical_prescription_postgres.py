"""PostgreSQL concurrency coverage for clinical prescriptions."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import os
from uuid import uuid4

import pytest
from sqlmodel import Session, create_engine, select

from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.auth.roles import Role
from vitta_one.clinical_prescription.service import (
    PrescriptionConflictError,
    PrescriptionNotFoundError,
    add_prescription_item,
    create_prescription,
    delete_prescription,
    remove_prescription_item,
    update_prescription_item,
)
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_prescription import Prescription, PrescriptionItem
from vitta_one.patient_queue.service import claim_next_patient, create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty

_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _cpf(prefix: str) -> str:
    digits = [int(char) for char in prefix]
    first_total = sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1)))
    first = (first_total * 10) % 11
    digits.append(0 if first == 10 else first)
    second_total = sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1)))
    second = (second_total * 10) % 11
    digits.append(0 if second == 10 else second)
    return "".join(str(digit) for digit in digits)


def _random_cpf() -> str:
    value = int(uuid4().hex[:10], 16) % 1_000_000_000
    prefix = f"{value:09d}"
    if len(set(prefix)) == 1:
        prefix = "123456789"
    return _cpf(prefix)


def _seed(engine):
    suffix = uuid4().hex[:10]
    base = datetime.now(timezone.utc)
    with Session(engine) as db:
        doctor = User(
            email=f"prescription-pg-{suffix}@example.invalid",
            password_hash="test-only-hash",
            role=Role.MEDICO.value,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)

        specialty = create_specialty(db, name=f"Prescription PG {suffix}")
        professional = create_professional(
            db,
            name=f"Dra. Prescription {suffix}",
            registration_identifier=f"CRM-PG-{suffix}",
            specialty_ids=[specialty.id],
            user_id=doctor.id,
        )
        patient = create_patient(
            db,
            name=f"Paciente Prescription {suffix}",
            cpf=_random_cpf(),
        )
        slot = create_availability_slot(
            db,
            professional_id=professional.id,
            starts_at=base + timedelta(days=5),
            now=base,
        )
        consultation = schedule_consultation(
            db,
            patient_id=patient.id,
            slot_id=slot.id,
            now=base,
        )
        entry = confirm_arrival(
            db,
            consultation_id=consultation.id,
            symptoms="Relato concorrente de prescrição",
            priority="VERDE",
            now=base + timedelta(minutes=5),
        )
        claim_next_patient(
            db,
            doctor_user_id=doctor.id,
            now=base + timedelta(minutes=10),
        )
        record = db.exec(
            select(ClinicalCareRecord).where(
                ClinicalCareRecord.consultation_id == consultation.id
            )
        ).one()
        return doctor.id, record.id, consultation.id, entry.id


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Prescription concurrency requires PostgreSQL.",
)
def test_concurrent_prescription_creation_never_leaves_empty_documents() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, record_id, _, _ = _seed(engine)

    def create(label: str):
        with Session(engine) as db:
            return create_prescription(
                db,
                clinical_care_record_id=record_id,
                doctor_user_id=doctor_id,
                medication_or_item=f"Item {label}",
                instructions=f"Orientação {label}",
            ).id

    with ThreadPoolExecutor(max_workers=2) as pool:
        created_ids = list(pool.map(create, ["A", "B"]))

    assert len(set(created_ids)) == 2
    with Session(engine) as db:
        documents = db.exec(
            select(Prescription).where(
                Prescription.clinical_care_record_id == record_id
            )
        ).all()
        assert len(documents) == 2
        for document in documents:
            children = db.exec(
                select(PrescriptionItem).where(
                    PrescriptionItem.prescription_id == document.id
                )
            ).all()
            assert len(children) == 1


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Prescription concurrency requires PostgreSQL.",
)
def test_concurrent_item_saves_are_serialized_to_complete_payload() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, record_id, _, _ = _seed(engine)
    with Session(engine) as db:
        prescription = create_prescription(
            db,
            clinical_care_record_id=record_id,
            doctor_user_id=doctor_id,
            medication_or_item="Base",
            instructions="Base",
        )
        prescription_id = prescription.id
        item_id = prescription.items[0].id

    payloads = [
        ("Medicamento A", "Orientação A", "Nota A"),
        ("Medicamento B", "Orientação B", "Nota B"),
    ]

    def save(payload):
        with Session(engine) as db:
            view = update_prescription_item(
                db,
                prescription_id=prescription_id,
                item_id=item_id,
                doctor_user_id=doctor_id,
                medication_or_item=payload[0],
                instructions=payload[1],
                notes=payload[2],
            )
            return view.items[0].medication_or_item

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(save, payloads))

    with Session(engine) as db:
        item = db.get(PrescriptionItem, item_id)
        assert item is not None
        stored = (item.medication_or_item, item.instructions, item.notes)
        assert stored in set(payloads)


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Prescription concurrency requires PostgreSQL.",
)
def test_concurrent_removals_cannot_empty_persisted_prescription() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, record_id, _, _ = _seed(engine)
    with Session(engine) as db:
        prescription = create_prescription(
            db,
            clinical_care_record_id=record_id,
            doctor_user_id=doctor_id,
            medication_or_item="Primeiro",
            instructions="Orientação 1",
        )
        prescription = add_prescription_item(
            db,
            prescription_id=prescription.id,
            doctor_user_id=doctor_id,
            medication_or_item="Segundo",
            instructions="Orientação 2",
        )
        prescription_id = prescription.id
        item_ids = [item.id for item in prescription.items]

    def remove(item_id: int):
        with Session(engine) as db:
            try:
                remove_prescription_item(
                    db,
                    prescription_id=prescription_id,
                    item_id=item_id,
                    doctor_user_id=doctor_id,
                )
                return "removed"
            except PrescriptionConflictError:
                return "kept"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(remove, item_ids))

    assert sorted(results) == ["kept", "removed"]
    with Session(engine) as db:
        remaining = db.exec(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == prescription_id
            )
        ).all()
        assert len(remaining) == 1


@pytest.mark.skipif(
    not _DATABASE_URL.startswith("postgresql"),
    reason="Prescription concurrency requires PostgreSQL.",
)
def test_concurrent_delete_is_idempotently_safe_and_leaves_no_orphans() -> None:
    engine = create_engine(_DATABASE_URL, pool_pre_ping=True)
    doctor_id, record_id, _, _ = _seed(engine)
    with Session(engine) as db:
        prescription = create_prescription(
            db,
            clinical_care_record_id=record_id,
            doctor_user_id=doctor_id,
            medication_or_item="Item",
            instructions="Orientação",
        )
        prescription_id = prescription.id

    def delete():
        with Session(engine) as db:
            try:
                delete_prescription(
                    db,
                    prescription_id=prescription_id,
                    doctor_user_id=doctor_id,
                )
                return "deleted"
            except PrescriptionNotFoundError:
                return "missing"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: delete(), range(2)))

    assert sorted(results) == ["deleted", "missing"]
    with Session(engine) as db:
        assert db.get(Prescription, prescription_id) is None
        assert db.exec(
            select(PrescriptionItem).where(
                PrescriptionItem.prescription_id == prescription_id
            )
        ).all() == []
