"""Persisted weekly clinic shifts and rolling 45-day slot publication.

Existing reservations and individually disabled/manual slots are never overwritten.
All local times are converted to UTC using the configured clinic timezone.
"""
from datetime import datetime, date, time, timedelta, timezone
import re
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select
from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus
from vitta_one.appointment_scheduling.service import SchedulingValidationError
from vitta_one.appointment_scheduling.settings import clinic_timezone
from vitta_one.appointment_scheduling.temporal import ensure_utc, parse_clinic_datetime_local, SchedulingTimeValidationError
from vitta_one.models.appointment import ProfessionalAvailabilitySlot, ProfessionalWeeklySchedule
from vitta_one.models.professional import Professional

BOOKING_DAYS = 45

def _minutes(value: str) -> int:
    if not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", str(value or "")):
        raise SchedulingValidationError("Informe o horário no formato HH:MM.")
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute

def _validate(start_day: int, end_day: int, start: str, end: str, duration: int) -> None:
    if not 0 <= start_day <= end_day <= 6:
        raise SchedulingValidationError("Escolha os dias de segunda a domingo em ordem crescente.")
    if duration not in (30, 60):
        raise SchedulingValidationError("Duração permitida: 30 ou 60 minutos.")
    begin, finish = _minutes(start), _minutes(end)
    if finish <= begin or finish - begin < duration:
        raise SchedulingValidationError("O fim do expediente precisa ser posterior ao início e comportar uma consulta.")
    if (finish - begin) % duration:
        raise SchedulingValidationError("O expediente deve corresponder a blocos completos de consulta.")

def weekly_schedule_matches_instant(db: Session, professional_id: int, starts_at: datetime) -> bool:
    rule = db.exec(select(ProfessionalWeeklySchedule).where(ProfessionalWeeklySchedule.professional_id == professional_id)).first()
    if rule is None:
        return False
    local = ensure_utc(starts_at).astimezone(clinic_timezone())
    minute = local.hour * 60 + local.minute
    begin, finish = _minutes(rule.time_start), _minutes(rule.time_end)
    return (rule.weekday_start <= local.weekday() <= rule.weekday_end
            and begin <= minute < finish
            and minute + rule.slot_minutes <= finish
            and (minute - begin) % rule.slot_minutes == 0)

def _desired(rule: ProfessionalWeeklySchedule, now: datetime) -> set[datetime]:
    zone = clinic_timezone()
    local_today = now.astimezone(zone).date()
    limit = now + timedelta(days=BOOKING_DAYS)
    begin, finish = _minutes(rule.time_start), _minutes(rule.time_end)
    result: set[datetime] = set()
    for day_delta in range(BOOKING_DAYS + 1):
        day = local_today + timedelta(days=day_delta)
        if not rule.weekday_start <= day.weekday() <= rule.weekday_end:
            continue
        for minute in range(begin, finish, rule.slot_minutes):
            local_string = f"{day.isoformat()}T{minute // 60:02d}:{minute % 60:02d}"
            try:
                starts = parse_clinic_datetime_local(local_string)
            except SchedulingTimeValidationError:
                continue  # nonexistent wall-clock time during DST transition
            if now < starts <= limit:
                result.add(starts)
    return result

def ensure_weekly_slots(db: Session, *, professional_id: int, now: datetime | None = None) -> int:
    """Idempotently roll materialized bookable slots forward; preserve manual choices."""
    timestamp = ensure_utc(now or datetime.now(timezone.utc))
    doctor = db.get(Professional, professional_id)
    if doctor is None or not doctor.is_active:
        return 0
    rule = db.exec(select(ProfessionalWeeklySchedule).where(ProfessionalWeeklySchedule.professional_id == professional_id)).first()
    if rule is None:
        return 0
    wanted = _desired(rule, timestamp)
    horizon = timestamp + timedelta(days=BOOKING_DAYS)
    existing = db.exec(select(ProfessionalAvailabilitySlot).where(
        ProfessionalAvailabilitySlot.professional_id == professional_id,
        ProfessionalAvailabilitySlot.starts_at > timestamp,
        ProfessionalAvailabilitySlot.starts_at <= horizon,
    )).all()
    present = {ensure_utc(slot.starts_at) for slot in existing}
    changed = False
    for slot in existing:
        if slot.is_weekly_generated and ensure_utc(slot.starts_at) not in wanted and slot.status == AvailabilitySlotStatus.AVAILABLE.value:
            slot.status = AvailabilitySlotStatus.INACTIVE.value
            slot.updated_at = timestamp
            db.add(slot)
            changed = True
    missing = sorted(wanted - present)
    if missing:
        rows = [dict(professional_id=professional_id, starts_at=starts, status=AvailabilitySlotStatus.AVAILABLE.value,
                     is_weekly_generated=True, created_at=timestamp, updated_at=timestamp) for starts in missing]
        if db.get_bind().dialect.name == "postgresql":
            statement = postgres_insert(ProfessionalAvailabilitySlot).values(rows).on_conflict_do_nothing(
                index_elements=["professional_id", "starts_at"])
            db.execute(statement)
        elif db.get_bind().dialect.name == "sqlite":
            statement = sqlite_insert(ProfessionalAvailabilitySlot).values(rows).on_conflict_do_nothing(
                index_elements=["professional_id", "starts_at"])
            db.execute(statement)
        else:
            for row in rows:
                db.add(ProfessionalAvailabilitySlot(**row))
        changed = True
    if changed:
        db.commit()
    return len(missing)

def save_weekly_schedule(db: Session, *, professional_id: int, weekday_start: int,
                         weekday_end: int, time_start: str, time_end: str,
                         slot_minutes: int = 30) -> int:
    """Upsert one doctor's recurring shift without cancelling reserved visits."""
    _validate(weekday_start, weekday_end, time_start, time_end, slot_minutes)
    professional = db.exec(select(Professional).where(Professional.id == professional_id).with_for_update()).first()
    if professional is None or not professional.is_active:
        raise SchedulingValidationError("Selecione um médico ativo.")
    rule = db.exec(select(ProfessionalWeeklySchedule).where(
        ProfessionalWeeklySchedule.professional_id == professional_id).with_for_update()).first()
    if rule is None:
        rule = ProfessionalWeeklySchedule(professional_id=professional_id, weekday_start=weekday_start,
                                          weekday_end=weekday_end, time_start=time_start,
                                          time_end=time_end, slot_minutes=slot_minutes)
    else:
        rule.weekday_start = weekday_start
        rule.weekday_end = weekday_end
        rule.time_start = time_start
        rule.time_end = time_end
        rule.slot_minutes = slot_minutes
        rule.updated_at = datetime.now(timezone.utc)
    db.add(rule)
    db.flush()
    published = ensure_weekly_slots(db, professional_id=professional_id)
    # Always persist edited shift rules, even when every slot already existed.
    db.commit()
    return published
