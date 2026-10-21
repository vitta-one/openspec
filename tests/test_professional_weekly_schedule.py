"""Unit coverage for persisted weekly doctors' working hours (not run in this change)."""
from datetime import datetime, timezone
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from vitta_one.appointment_scheduling.service import SchedulingValidationError, release_reserved_slot
from vitta_one.appointment_scheduling.weekly import save_weekly_schedule, ensure_weekly_slots
from vitta_one.models.appointment import ProfessionalAvailabilitySlot, ProfessionalWeeklySchedule
from vitta_one.models.professional import Professional

@pytest.fixture
def db(monkeypatch):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()

def new_doctor(db):
    row = Professional(name="Dra. Agenda QA", registration_identifier="INT-WEEKLY-QA", is_active=True)
    db.add(row); db.commit(); db.refresh(row)
    return row

def test_weekly_hours_materialize_idempotent_available_slots(db):
    doctor = new_doctor(db)
    count = save_weekly_schedule(db, professional_id=doctor.id, weekday_start=0,
                                 weekday_end=4, time_start="08:00", time_end="12:00",
                                 slot_minutes=30)
    assert count > 0
    slots = db.exec(select(ProfessionalAvailabilitySlot).where(
        ProfessionalAvailabilitySlot.professional_id == doctor.id)).all()
    assert all(item.is_weekly_generated and item.status == "AVAILABLE" for item in slots)
    assert ensure_weekly_slots(db, professional_id=doctor.id) == 0
    assert len(slots) == len(db.exec(select(ProfessionalAvailabilitySlot).where(
        ProfessionalAvailabilitySlot.professional_id == doctor.id)).all())

def test_reservations_survive_shift_changes(db):
    doctor = new_doctor(db)
    save_weekly_schedule(db, professional_id=doctor.id, weekday_start=0,
                         weekday_end=6, time_start="08:00", time_end="12:00")
    slots = db.exec(select(ProfessionalAvailabilitySlot).where(
        ProfessionalAvailabilitySlot.professional_id == doctor.id)).all()
    assert len(slots) > 3
    reserved = slots[0]
    reserved.status = "BOOKED"
    db.add(reserved); db.commit()
    save_weekly_schedule(db, professional_id=doctor.id, weekday_start=0,
                         weekday_end=6, time_start="14:00", time_end="18:00")
    db.refresh(reserved)
    assert reserved.status == "BOOKED"
    released_at = datetime.now(timezone.utc)
    release_reserved_slot(db, reserved, now=released_at)
    assert reserved.status == "INACTIVE"
    assert any(item.status == "INACTIVE" for item in slots[1:])

@pytest.mark.parametrize("start,end,time_start,time_end", [
    (5, 2, "08:00", "18:00"),
    (0, 4, "20:00", "08:00"),
    (0, 4, "08:00", "08:15"),
])
def test_invalid_weekly_rule_rejected(db, start, end, time_start, time_end):
    doctor = new_doctor(db)
    with pytest.raises(SchedulingValidationError):
        save_weekly_schedule(db, professional_id=doctor.id, weekday_start=start,
                             weekday_end=end, time_start=time_start, time_end=time_end)
