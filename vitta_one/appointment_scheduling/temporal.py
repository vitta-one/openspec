"""Clinic-local datetime parsing and UTC persistence helpers."""

from datetime import date, datetime, time, timedelta, timezone

from vitta_one.appointment_scheduling.settings import clinic_timezone


class SchedulingTimeValidationError(ValueError):
    """Raised when a date/time supplied to scheduling is invalid."""


def ensure_utc(value: datetime) -> datetime:
    # SQLite used by unit tests can drop tzinfo on round-trip; persisted values
    # are UTC by contract. User-facing local input never passes through here.
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_clinic_datetime_local(value: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise SchedulingTimeValidationError("Informe a data e o horário.")
    try:
        local_naive = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SchedulingTimeValidationError("Informe uma data e horário válidos.") from exc
    if local_naive.tzinfo is not None:
        raise SchedulingTimeValidationError(
            "Informe o horário local da clínica sem timezone embutido."
        )

    zone = clinic_timezone()
    local = local_naive.replace(tzinfo=zone, fold=0)
    round_trip = local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    if round_trip != local_naive:
        raise SchedulingTimeValidationError(
            "Este horário local não existe no timezone configurado da clínica."
        )
    return local.astimezone(timezone.utc)


def clinic_date_range_to_utc(
    start_value: str | None,
    end_value: str | None,
) -> tuple[datetime | None, datetime | None]:
    zone = clinic_timezone()
    start_utc: datetime | None = None
    end_utc: datetime | None = None

    if str(start_value or "").strip():
        try:
            start_date = date.fromisoformat(str(start_value).strip())
        except ValueError as exc:
            raise SchedulingTimeValidationError("A data inicial é inválida.") from exc
        start_utc = datetime.combine(start_date, time.min, zone).astimezone(timezone.utc)

    if str(end_value or "").strip():
        try:
            end_date = date.fromisoformat(str(end_value).strip())
        except ValueError as exc:
            raise SchedulingTimeValidationError("A data final é inválida.") from exc
        end_exclusive = end_date + timedelta(days=1)
        end_utc = datetime.combine(end_exclusive, time.min, zone).astimezone(timezone.utc)

    if start_utc and end_utc and start_utc >= end_utc:
        raise SchedulingTimeValidationError(
            "A data final precisa ser igual ou posterior à data inicial."
        )
    return start_utc, end_utc


def format_clinic_datetime(value: datetime) -> str:
    return ensure_utc(value).astimezone(clinic_timezone()).strftime("%d/%m/%Y às %H:%M")


def clinic_today_iso(now: datetime | None = None) -> str:
    current = ensure_utc(now or datetime.now(timezone.utc))
    return current.astimezone(clinic_timezone()).date().isoformat()


def clinic_date_after_iso(days: int, now: datetime | None = None) -> str:
    current = ensure_utc(now or datetime.now(timezone.utc))
    return (current.astimezone(clinic_timezone()).date() + timedelta(days=days)).isoformat()
