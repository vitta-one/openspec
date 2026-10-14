"""Authorization boundary for operational read-only receptionist dashboard."""
from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from vitta_one.reception.dashboard.service import ReceptionOverview, get_reception_overview


def reception_overview(db: Session, *, token: str) -> ReceptionOverview:
    require_role(db, token, Role.RECEPCIONISTA)
    return get_reception_overview(db)
