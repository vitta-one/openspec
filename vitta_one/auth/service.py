"""Identity, session, and bootstrap services."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from vitta_one.auth.roles import Role
from vitta_one.auth.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    normalize_email,
    verify_password,
)
from vitta_one.models.auth import AuthSession, User


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Sanitized authenticated identity returned to the application layer."""

    id: int
    email: str
    role: Role


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Result of the first-administrator bootstrap operation."""

    created: bool
    user_id: int


class BootstrapConflictError(RuntimeError):
    """Raised when bootstrap would overwrite or reinterpret an existing identity."""


def utc_now() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(timezone.utc)


def find_user_by_email(db: Session, email: str) -> User | None:
    """Find a user by the normalized login e-mail."""
    normalized = normalize_email(email)
    if not normalized:
        return None
    return db.exec(select(User).where(User.email == normalized)).first()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate local credentials and return the matching user when valid."""
    user = find_user_by_email(db, email)
    if user is None or not verify_password(user.password_hash, password):
        return None

    try:
        Role(user.role)
    except ValueError:
        return None

    return user


def create_session(
    db: Session,
    *,
    user_id: int,
    ttl: timedelta,
    now: datetime | None = None,
) -> str:
    """Create a revocable server-side session and return only its raw client token."""
    if ttl.total_seconds() <= 0:
        raise ValueError("A duração da sessão deve ser positiva.")

    issued_at = now or utc_now()
    token = new_session_token()
    db.add(
        AuthSession(
            user_id=user_id,
            token_hash=hash_session_token(token),
            created_at=issued_at,
            expires_at=issued_at + ttl,
        )
    )
    db.commit()
    return token


def resolve_session(
    db: Session,
    token: str,
    *,
    now: datetime | None = None,
) -> AuthenticatedUser | None:
    """Resolve a valid non-revoked session to a sanitized authenticated identity."""
    if not token:
        return None

    session_row = db.exec(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(token))
    ).first()
    if session_row is None or session_row.revoked_at is not None:
        return None

    current_time = now or utc_now()
    if session_row.expires_at <= current_time:
        return None

    user = db.get(User, session_row.user_id)
    if user is None:
        return None

    try:
        role = Role(user.role)
    except ValueError:
        return None

    if user.id is None:
        return None

    return AuthenticatedUser(id=user.id, email=user.email, role=role)


def revoke_session(
    db: Session,
    token: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Revoke an opaque session token without exposing it in persistence or logs."""
    if not token:
        return False

    session_row = db.exec(
        select(AuthSession).where(AuthSession.token_hash == hash_session_token(token))
    ).first()
    if session_row is None:
        return False
    if session_row.revoked_at is not None:
        return True

    session_row.revoked_at = now or utc_now()
    db.add(session_row)
    db.commit()
    return True


def bootstrap_first_admin(db: Session, *, email: str, password: str) -> BootstrapResult:
    """Create the first Administrator exactly once without overwriting identities."""
    normalized_email = normalize_email(email)
    if not normalized_email:
        raise ValueError("O e-mail do administrador é obrigatório.")
    if not password:
        raise ValueError("A senha do administrador é obrigatória.")

    existing_admin = db.exec(
        select(User).where(User.role == Role.ADMINISTRADOR.value)
    ).first()
    if existing_admin is not None:
        if existing_admin.id is None:
            raise RuntimeError("Administrador existente sem identificador persistido.")
        return BootstrapResult(created=False, user_id=existing_admin.id)

    existing_identity = find_user_by_email(db, normalized_email)
    if existing_identity is not None:
        raise BootstrapConflictError(
            "O e-mail informado já pertence a uma identidade existente."
        )

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role=Role.ADMINISTRADOR.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user.id is None:
        raise RuntimeError("Não foi possível obter o identificador do administrador criado.")
    return BootstrapResult(created=True, user_id=user.id)
