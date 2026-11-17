"""Authorization boundary for operational read-only receptionist dashboard."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.appointment_scheduling.temporal import (
    clinic_date_range_to_utc,
    clinic_today_iso,
    ensure_utc,
)
from vitta_one.models.notification import EmailNotification
from vitta_one.reception.dashboard.service import (
    ReceptionDaySnapshot,
    ReceptionOverview,
    get_reception_day,
    get_reception_overview,
)


@dataclass(frozen=True, slots=True)
class ReceptionEmailMetrics:
    """Status counts only; recipient and message metadata never leave the query."""

    accepted: int = 0
    delivered: int = 0
    failed: int = 0
    pending: int = 0


def reception_email_metrics(
    db: Session, *, token: str, now: datetime | None = None
) -> ReceptionEmailMetrics:
    """Count agenda message states over the 30 most recent clinic-local dates."""
    require_role(db, token, Role.RECEPCIONISTA)
    current = ensure_utc(now or datetime.now(timezone.utc))
    local_today = date.fromisoformat(clinic_today_iso(current))
    first_date = local_today - timedelta(days=29)
    start, end = clinic_date_range_to_utc(first_date.isoformat(), local_today.isoformat())
    assert start is not None and end is not None

    grouped = db.exec(
        select(EmailNotification.status, func.count(EmailNotification.id))
        .where(
            EmailNotification.kind.in_(
                (
                    "booking_confirmed",
                    "booking_rescheduled",
                    "booking_cancelled",
                    "booking_reminder",
                )
            ),
            EmailNotification.created_at >= start,
            EmailNotification.created_at < end,
        )
        .group_by(EmailNotification.status)
    ).all()

    totals = {"ACCEPTED": 0, "DELIVERED": 0, "FAILED": 0, "PENDING": 0}
    for status, count in grouped:
        if status == "ACCEPTED":
            totals["ACCEPTED"] += int(count)
        elif status == "DELIVERED":
            totals["DELIVERED"] += int(count)
        elif status == "FAILED":
            totals["FAILED"] += int(count)
        elif status != "SUPPRESSED":
            # PENDING/SENDING/UNKNOWN/NOT_CONFIGURED and future unresolved
            # states stay visible as pending or indeterminate.
            totals["PENDING"] += int(count)

    return ReceptionEmailMetrics(
        accepted=totals["ACCEPTED"],
        delivered=totals["DELIVERED"],
        failed=totals["FAILED"],
        pending=totals["PENDING"],
    )


def reception_overview(db: Session, *, token: str) -> ReceptionOverview:
    require_role(db, token, Role.RECEPCIONISTA)
    return get_reception_overview(db)


def reception_day_operations(
    db: Session,
    *,
    token: str,
    professional_id: int | None = None,
    search: str = "",
    page: int = 1,
    page_size: int = 7,
) -> ReceptionDaySnapshot:
    """Authorize the receptionist before returning a filtered daily table."""
    require_role(db, token, Role.RECEPCIONISTA)
    return get_reception_day(
        db,
        professional_id=professional_id,
        search=search,
        page=page,
        page_size=page_size,
    )
