"""Disposable PostgreSQL test fixtures for real-browser prescription QA.

Only run against the isolated GitHub Actions database. Never run with production
credentials: the script intentionally adds synthetic identities and clinical data.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session, create_engine

from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.clinical_prescription.service import create_prescription
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.auth import User
from vitta_one.patient_queue.service import claim_next_patient, create_patient
from vitta_one.professional_directory.service import create_professional, create_specialty


def _cpf(prefix: str) -> str:
    digits = [int(char) for char in prefix]
    first = (sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1))) * 10) % 11
    digits.append(0 if first == 10 else first)
    second = (sum(digit * weight for digit, weight in zip(digits, range(11, 1, -1))) * 10) % 11
    digits.append(0 if second == 10 else second)
    return "".join(str(digit) for digit in digits)


def main() -> None:
    if os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes":
        raise RuntimeError("QA only permitted on an explicitly declared disposable database")
    database_url = os.environ["DATABASE_URL"]
    if not database_url.startswith("postgresql+psycopg://") or "localhost:5432/vitta_one" not in database_url:
        raise RuntimeError("Refusing QA fixture creation outside local CI PostgreSQL")
    password = os.environ["VITTA_ONE_QA_PASSWORD"]
    now = datetime.now(timezone.utc)
    engine = create_engine(database_url)
    with Session(engine) as db:
        doctors = []
        for code in ("a", "b"):
            user = User(
                email=f"qa-doctor-{code}@example.invalid",
                password_hash=hash_password(password),
                role=Role.MEDICO.value,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            doctors.append(user)
        doctor = doctors[0]
        specialty = create_specialty(db, name="Medicina QA Navegador")
        professional = create_professional(
            db, name="Dra. QA Navegador", registration_identifier="CRM-QA-2026",
            specialty_ids=[specialty.id], user_id=doctor.id,
        )
        patient = create_patient(db, name="Paciente Fictício QA Navegador", cpf=_cpf("123456789"))
        slot = create_availability_slot(
            db, professional_id=professional.id, starts_at=now + timedelta(days=5), now=now
        )
        consultation = schedule_consultation(
            db, patient_id=patient.id, slot_id=slot.id, now=now
        )
        confirm_arrival(
            db, consultation_id=consultation.id, symptoms="Sintoma fictício QA",
            priority="VERDE", now=now + timedelta(minutes=5)
        )
        from sqlmodel import select
        from vitta_one.models.clinical_care import ClinicalCareRecord
        claim_next_patient(db, doctor_user_id=doctor.id, now=now + timedelta(minutes=10))
        record = db.exec(
            select(ClinicalCareRecord).where(ClinicalCareRecord.consultation_id == consultation.id)
        ).one()
        prescription = create_prescription(
            db, clinical_care_record_id=record.id, doctor_user_id=doctor.id,
            medication_or_item="Medicamento Fictício QA",
            instructions="Uso fictício, somente para testes de software",
            notes="Observação fictícia", general_notes="Não é uma prescrição clínica real",
        )
        fixture = {
            "prescription_id": prescription.id,
            "patient_name": patient.name,
            "doctor_a_email": doctors[0].email,
            "doctor_b_email": doctors[1].email,
        }
    path = Path("qa-artifacts/fixture.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    print("Fixture sintética criada: duas identidades médicas, consulta ativa e prescrição (sem dados pessoais reais).")


if __name__ == "__main__":
    main()
