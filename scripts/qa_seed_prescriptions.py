"""Disposable PostgreSQL test fixtures for real-browser prescription QA.

Only run against the isolated GitHub Actions database. Never run with production
credentials: the script intentionally adds synthetic identities and clinical data.
"""
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session, create_engine

from vitta_one.appointment_scheduling.service import create_availability_slot, schedule_consultation
from vitta_one.appointment_scheduling.temporal import clinic_date_range_to_utc, clinic_today_iso
from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.clinical_prescription.service import add_prescription_item, create_prescription
from vitta_one.consultation_care.service import confirm_arrival
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.professional import Professional
from sqlmodel import select
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import PatientPortalInvitation
from vitta_one.patient_queue.service import claim_next_patient, create_patient, create_queue_entry, finish_queue_entry
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
        admin = User(
            email="qa-admin-directory@example.invalid",
            password_hash=hash_password(password),
            role=Role.ADMINISTRADOR.value,
        )
        db.add(admin)
        receptionist = User(
            email="qa-reception-dashboard@example.invalid",
            password_hash=hash_password(password),
            role=Role.RECEPCIONISTA.value,
        )
        db.add(receptionist)
        db.commit()
        specialty = create_specialty(db, name="Medicina QA Navegador")
        for number in range(1, 13):
            create_specialty(db, name=f"Especialidade QA Extra {number}")
        extra_professionals = []
        for number in range(1, 5):
            extra_professionals.append(
                create_professional(
                    db, name=f"Dr. QA Extra {number}",
                    registration_identifier=f"INT-QA-{number}",
                    specialty_ids=[specialty.id], user_id=None,
                )
            )
        professional = create_professional(
            db, name="Dra. QA Navegador", registration_identifier="CRM-QA-2026",
            specialty_ids=[specialty.id], user_id=doctor.id,
        )
        patient = create_patient(db, name="Paciente Fictício QA Navegador", cpf=_cpf("123456789"))

        # Synthetic daily rows exercise the receptionist's table and filters.
        clinic_date = clinic_today_iso(now)
        day_start, day_end = clinic_date_range_to_utc(clinic_date, clinic_date)
        assert day_start is not None and day_end is not None
        daily_start = day_start + timedelta(hours=8)
        daily_professionals = [professional, *extra_professionals[:2]]
        daily_statuses = (
            "CONCLUIDA",
            "CONCLUIDA",
            "EM_ANDAMENTO",
            "CONFIRMADA",
            "CONFIRMADA",
            "AGENDADA",
            "CANCELADA",
        )
        day_first_patient_name = ""
        day_first_patient_phone = ""
        for number in range(1, 25):
            daily_patient = create_patient(
                db,
                name=f"Paciente QA Operação {number:02d}",
                cpf=_cpf(f"876{number:06d}"),
                phone=f"119{number:08d}",
            )
            if number == 1:
                day_first_patient_name = daily_patient.name
                day_first_patient_phone = daily_patient.phone or ""
            starts_at = daily_start + timedelta(minutes=30 * (number - 1))
            if starts_at >= day_end:
                raise RuntimeError("Synthetic daily QA appointments exceed the clinic day.")
            daily_professional = daily_professionals[(number - 1) % len(daily_professionals)]
            slot = ProfessionalAvailabilitySlot(
                professional_id=daily_professional.id,
                starts_at=starts_at,
                status="BOOKED",
            )
            db.add(slot)
            db.flush()
            db.add(
                Consultation(
                    patient_id=daily_patient.id,
                    professional_id=daily_professional.id,
                    availability_slot_id=slot.id,
                    scheduled_at=starts_at,
                    status=daily_statuses[(number - 1) % len(daily_statuses)],
                )
            )
            db.commit()
        # Preserve a completed historical encounter for responsive history QA.
        old_slot = create_availability_slot(
            db, professional_id=professional.id, starts_at=now + timedelta(days=4), now=now
        )
        old_consultation = schedule_consultation(
            db, patient_id=patient.id, slot_id=old_slot.id, now=now
        )
        old_entry = confirm_arrival(
            db, consultation_id=old_consultation.id, symptoms="Sintoma histórico fictício QA",
            priority="VERDE", now=now + timedelta(minutes=3)
        )
        claim_next_patient(db, doctor_user_id=doctor.id, now=now + timedelta(minutes=4))
        from sqlmodel import select
        from vitta_one.models.clinical_care import ClinicalCareRecord
        old_record = db.exec(
            select(ClinicalCareRecord).where(ClinicalCareRecord.consultation_id == old_consultation.id)
        ).one()
        create_prescription(
            db, clinical_care_record_id=old_record.id, doctor_user_id=doctor.id,
            medication_or_item="Histórico Fictício QA", instructions="Orientação histórica fictícia",
            general_notes="Observação histórica fictícia",
        )
        finish_queue_entry(
            db, entry_id=old_entry.id, doctor_user_id=doctor.id, now=now + timedelta(minutes=9)
        )
        # Create a second, active encounter for the same patient.
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
        add_prescription_item(
            db, prescription_id=prescription.id, doctor_user_id=doctor.id,
            medication_or_item="Segundo item fictício QA",
            instructions="Segunda orientação fictícia",
        )
        # A separate, unscheduled emergency-care journey for Chromium QA.
        # Doctor B is deliberately independent from Doctor A's booked appointment.
        create_professional(
            db,
            name="Dr. QA Pronto Atendimento",
            registration_identifier="CRM-QA-WALKIN",
            specialty_ids=[specialty.id],
            user_id=doctors[1].id,
        )
        walkin_patient = create_patient(
            db,
            name="Paciente QA Pronto Atendimento",
            cpf=_cpf("447588126"),
        )
        walkin_entry = create_queue_entry(
            db,
            patient_id=walkin_patient.id,
            symptoms="Relato sintético de pronto-socorro QA",
            priority="VERMELHO",
            now=now + timedelta(minutes=12),
        )
        assert walkin_entry.consultation_id is None

        # CI-only invitation: real HTTP activation and login through the browser,
        # while outbound email remains a separate provider integration gate.
        booking_email = "qa-booking-patient@example.invalid"
        booking_code = "synthetic-activation-code-qa-2026"
        booking_patient = create_patient(
            db, name="Paciente QA Autogendamento", cpf=_cpf("538176249"),
        )
        db.add(
            PatientPortalInvitation(
                patient_id=booking_patient.id,
                email=booking_email,
                code_hash=hashlib.sha256(booking_code.encode("utf-8")).hexdigest(),
                created_by_user_id=receptionist.id,
                consented_at=now,
                created_at=now,
                expires_at=now + timedelta(hours=24),
                delivery_status="ACCEPTED",
                sent_at=now,
            )
        )
        db.commit()
        booking_slot = create_availability_slot(
            db, professional_id=db.exec(
                select(Professional).where(Professional.user_id == doctors[1].id)
            ).one().id,
            starts_at=now + timedelta(days=2), now=now,
        )

        fixture = {
            "prescription_id": prescription.id,
            "patient_name": patient.name,
            "doctor_a_email": doctors[0].email,
            "doctor_b_email": doctors[1].email,
            "walkin_patient_name": walkin_patient.name,
            "walkin_entry_id": walkin_entry.id,
            "booking_patient_email": booking_email,
            "booking_activation_code": booking_code,
            "booking_patient_name": booking_patient.name,
            "booking_doctor_name": "Dr. QA Pronto Atendimento",
            "booking_specialty_name": specialty.name,
            "booking_slot_id": booking_slot.id,
            "admin_email": admin.email,
            "reception_email": receptionist.email,
            "day_first_patient_name": day_first_patient_name,
            "day_first_patient_phone": day_first_patient_phone,
            "day_first_professional_name": daily_professionals[0].name,
            "day_total": 24,
        }
    path = Path("qa-artifacts/fixture.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    print("Fixture sintética criada: identidades QA, 24 consultas do dia e prescrição (sem dados pessoais reais).")


if __name__ == "__main__":
    main()
