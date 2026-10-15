"""Authorization boundary for operational read-only receptionist dashboard."""
from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.reception.dashboard.service import (
    ReceptionDaySnapshot,
    ReceptionOverview,
    get_reception_day,
    get_reception_overview,
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
