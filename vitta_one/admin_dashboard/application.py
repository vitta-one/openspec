"""Server-authorized application boundary for administrative dashboard reads."""
from datetime import datetime

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from .service import AdminDashboardSnapshot, get_admin_dashboard_snapshot


def admin_dashboard_snapshot(
    db: Session, *, token: str, now: datetime | None = None
) -> AdminDashboardSnapshot:
    """Revalidate the administrator session before returning aggregate values."""
    require_role(db, token, Role.ADMINISTRADOR)
    return get_admin_dashboard_snapshot(db, now=now)
