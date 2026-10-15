"""Tests for the receptionist's persisted daily operations table."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.authorization import AuthenticationRequiredError, RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional, ProfessionalSpecialty, Specialty
from vitta_one.patient_queue.application import reception_search_patients
from vitta_one.patient_queue.service import (
    PatientValidationError,
    create_patient,
    search_patient_identities,
)
from vitta_one.reception.dashboard.application import reception_day_operations
from vitta_one.reception.dashboard.service import get_reception_day


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
    engine.dispose()


def make_professional(db, index: int = 1, *, name: str = "Dra. Clara Silveira"):
    professional = Professional(
        name=name,
        registration_identifier=f"CRM-TEST-{index}",
    )
    db.add(professional)
    db.commit()
    db.refresh(professional)
    return professional


def add_consultation(
    db,
    professional,
    *,
    patient_name: str,
    cpf: str,
    scheduled_at: datetime,
    status: str = "AGENDADA",
    phone: str | None = None,
):
    patient = Patient(name=patient_name, cpf=cpf, phone=phone)
    db.add(patient)
    db.commit()
    db.refresh(patient)

    slot = ProfessionalAvailabilitySlot(
        professional_id=professional.id,
        starts_at=scheduled_at,
        status="BOOKED",
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    consultation = Consultation(
        patient_id=patient.id,
        professional_id=professional.id,
        availability_slot_id=slot.id,
        scheduled_at=scheduled_at,
        status=status,
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)
    return consultation, patient


def test_day_table_paginates_seven_real_consultations_and_keeps_statuses(db):
    now = datetime(2026, 10, 14, 15, tzinfo=timezone.utc)
    professional = make_professional(db)
    specialty = Specialty(name="Cardiologia", normalized_name="cardiologia")
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    db.add(
        ProfessionalSpecialty(
            professional_id=professional.id,
            specialty_id=specialty.id,
        )
    )
    db.commit()

    items = []
    for index in range(9):
        items.append(
            add_consultation(
                db,
                professional,
                patient_name=f"Paciente {index:02d}",
                cpf=f"{index + 1:011d}",
                phone=f"119845211{index:02d}",
                scheduled_at=datetime(
                    2026, 10, 14, 15, index * 5, tzinfo=timezone.utc
                ),
                status="CANCELADA" if index == 8 else "AGENDADA",
            )[0]
        )

    first = get_reception_day(db, now=now)
    second = get_reception_day(db, now=now, page=2)
    beyond_last = get_reception_day(db, now=now, page=99)

    assert first.clinic_date == "2026-10-14"
    assert first.total == 9
    assert first.page == 1 and first.total_pages == 2
    assert [row.id for row in first.appointments] == [item.id for item in items[:7]]
    assert first.appointments[0].specialty_names == ("Cardiologia",)
    assert len(second.appointments) == 2
    assert second.appointments[-1].status.value == "CANCELADA"
    assert beyond_last.page == 2
    assert all(not hasattr(row, "symptoms") for row in first.appointments)


def test_day_table_filters_by_professional_name_phone_and_cpf(db):
    now = datetime(2026, 10, 14, 15, tzinfo=timezone.utc)
    first_professional = make_professional(db, 1, name="Dra. Beatriz")
    second_professional = make_professional(db, 2, name="Dr. Marcos")
    target, patient = add_consultation(
        db,
        first_professional,
        patient_name="Helena Castro Nogueira",
        cpf="52998224725",
        phone="11984521102",
        scheduled_at=datetime(2026, 10, 14, 16, tzinfo=timezone.utc),
    )
    add_consultation(
        db,
        second_professional,
        patient_name="Outro Paciente",
        cpf="11144477735",
        phone=None,
        scheduled_at=datetime(2026, 10, 14, 16, 30, tzinfo=timezone.utc),
    )

    by_name = get_reception_day(db, now=now, search="helena")
    by_phone = get_reception_day(db, now=now, search="(11) 98452-1102")
    by_cpf = get_reception_day(db, now=now, search="529.982.247-25")
    by_professional = get_reception_day(
        db, now=now, professional_id=first_professional.id
    )

    assert [row.id for row in by_name.appointments] == [target.id]
    assert [row.id for row in by_phone.appointments] == [target.id]
    assert [row.id for row in by_cpf.appointments] == [target.id]
    assert [row.id for row in by_professional.appointments] == [target.id]
    assert by_name.appointments[0].patient_phone == patient.phone


def test_day_table_uses_clinic_local_date_boundaries(db):
    professional = make_professional(db)
    before, _ = add_consultation(
        db,
        professional,
        patient_name="Antes do dia",
        cpf="00000000001",
        scheduled_at=datetime(2026, 10, 14, 2, 59, 59, tzinfo=timezone.utc),
    )
    first, _ = add_consultation(
        db,
        professional,
        patient_name="Início do dia",
        cpf="00000000002",
        scheduled_at=datetime(2026, 10, 14, 3, 0, tzinfo=timezone.utc),
    )
    after, _ = add_consultation(
        db,
        professional,
        patient_name="Dia seguinte",
        cpf="00000000003",
        scheduled_at=datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc),
    )

    snapshot = get_reception_day(
        db,
        now=datetime(2026, 10, 14, 15, tzinfo=timezone.utc),
    )

    assert [row.id for row in snapshot.appointments] == [first.id]
    assert before.id not in {row.id for row in snapshot.appointments}
    assert after.id not in {row.id for row in snapshot.appointments}


def test_patient_phone_is_optional_normalized_and_validated(db):
    patient = create_patient(
        db,
        name="  Helena   Castro ",
        cpf="529.982.247-25",
        phone="(11) 98452-1102",
    )
    without_phone = create_patient(
        db,
        name="Paciente sem telefone",
        cpf="111.444.777-35",
    )

    assert patient.phone == "11984521102"
    assert without_phone.phone is None
    with pytest.raises(PatientValidationError, match="telefone"):
        create_patient(
            db,
            name="Telefone inválido",
            cpf="935.411.347-80",
            phone="123",
        )




def test_quick_search_returns_only_minimal_patient_identity(db):
    patient = create_patient(
        db,
        name="Helena Castro Nogueira",
        cpf="529.982.247-25",
        phone="(11) 98452-1102",
    )

    by_name = search_patient_identities(db, query="helena")
    by_phone = search_patient_identities(db, query="(11) 98452-1102")
    by_cpf = search_patient_identities(db, query="529.982.247-25")

    assert [item.id for item in by_name] == [patient.id]
    assert [item.id for item in by_phone] == [patient.id]
    assert [item.id for item in by_cpf] == [patient.id]
    assert not hasattr(by_name[0], "cpf")
    assert not hasattr(by_name[0], "clinical_history")

def test_day_table_application_requires_reception_role(db):
    receptionist = User(
        email="day-reception@example.invalid",
        password_hash="unused",
        role=Role.RECEPCIONISTA.value,
    )
    doctor = User(
        email="day-doctor@example.invalid",
        password_hash="unused",
        role=Role.MEDICO.value,
    )
    db.add(receptionist)
    db.add(doctor)
    db.commit()
    db.refresh(receptionist)
    db.refresh(doctor)
    reception_token = create_session(
        db, user_id=receptionist.id, ttl=timedelta(hours=1)
    )
    doctor_token = create_session(db, user_id=doctor.id, ttl=timedelta(hours=1))

    assert reception_day_operations(db, token=reception_token).total == 0
    with pytest.raises(AuthenticationRequiredError):
        reception_day_operations(db, token="")
    with pytest.raises(RoleForbiddenError):
        reception_day_operations(db, token=doctor_token)
    with pytest.raises(RoleForbiddenError):
        reception_search_patients(db, token=doctor_token, query="Helena")
