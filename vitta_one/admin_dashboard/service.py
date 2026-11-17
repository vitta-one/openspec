"""Non-clinical aggregate metrics for the administration home page."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, select

from vitta_one.appointment_scheduling.temporal import (
    clinic_date_range_to_utc,
    clinic_today_iso,
    ensure_utc,
)
from vitta_one.auth.roles import Role
from vitta_one.models.appointment import Consultation
from vitta_one.models.auth import User
from vitta_one.models.professional import Professional, Specialty


@dataclass(frozen=True, slots=True)
class AdminDashboardSnapshot:
    """Aggregate-only dashboard values; no patient or clinical data is returned."""

    active_professionals: int
    active_specialties: int
    consultations_today: int
    staff_accounts: int
    clinic_date: str


def get_admin_dashboard_snapshot(
    db: Session, *, now: datetime | None = None
) -> AdminDashboardSnapshot:
    """Count persisted directory records and today's non-cancelled appointments."""
    current = ensure_utc(now or datetime.now(timezone.utc))
    clinic_date = clinic_today_iso(current)
    start, end = clinic_date_range_to_utc(clinic_date, clinic_date)
    assert start is not None and end is not None

    active_professionals = int(
        db.exec(
            select(func.count(Professional.id)).where(Professional.is_active.is_(True))
        ).one()
        or 0
    )
    active_specialties = int(
        db.exec(
            select(func.count(Specialty.id)).where(Specialty.is_active.is_(True))
        ).one()
        or 0
    )
    consultations_today = int(
        db.exec(
            select(func.count(Consultation.id)).where(
                Consultation.scheduled_at >= start,
                Consultation.scheduled_at < end,
                Consultation.status != "CANCELADA",
            )
        ).one()
        or 0
    )
    staff_accounts = int(
        db.exec(
            select(func.count(User.id)).where(
                User.role.in_((Role.MEDICO.value, Role.RECEPCIONISTA.value))
            )
        ).one()
        or 0
    )

    return AdminDashboardSnapshot(
        active_professionals=active_professionals,
        active_specialties=active_specialties,
        consultations_today=consultations_today,
        staff_accounts=staff_accounts,
        clinic_date=clinic_date,
    )
