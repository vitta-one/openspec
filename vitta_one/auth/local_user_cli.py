"""Criação interativa de contas de demonstração no PostgreSQL QA local.

Nunca é uma alternativa ao cadastro/autorização da aplicação em produção.
Execute exclusivamente via `make user` dentro do ambiente de desenvolvimento.
"""

from getpass import getpass
import os
import sys

import reflex as rx
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.local_qa import LocalQaAccountError
from vitta_one.auth.roles import Role
from vitta_one.auth.security import (
    hash_password,
    is_valid_email_identifier,
    normalize_email,
)
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional


def require_isolated_local_database() -> None:
    """Recuse execução fora do banco QA isolado e da configuração do Make."""
    try:
        url = make_url(os.environ.get("DATABASE_URL", ""))
    except (ValueError, KeyError):
        raise LocalQaAccountError("DATABASE_URL local inválida.") from None

    safe = (
        os.environ.get("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "").lower() == "true"
        and os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes"
        and url.drivername == "postgresql+psycopg"
        and url.host == "127.0.0.1"
        and url.port == 5433
        and url.database == "vitta_one_qa"
        and url.username == "vittaqa"
        and bool(url.password)
        and url.password == os.environ.get("POSTGRES_PASSWORD")
        and os.environ.get("POSTGRES_USER") == "vittaqa"
        and os.environ.get("POSTGRES_DB") == "vitta_one_qa"
    )
    if not safe:
        raise LocalQaAccountError(
            "Criação recusada: use apenas o QA PostgreSQL local via make user."
        )


def create_local_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: Role,
    linked_id: int | None = None,
    patient_consent_confirmed: bool = False,
) -> User:
    """Crie uma conta nova; vínculos necessários são atômicos com a identidade."""
    require_isolated_local_database()
    if not isinstance(role, Role):
        raise LocalQaAccountError("Perfil inválido.")

    normalized = normalize_email(email)
    if (
        not is_valid_email_identifier(normalized)
        or "." not in normalized.rsplit("@", 1)[1]
    ):
        raise LocalQaAccountError("Informe um e-mail válido.")
    if not 12 <= len(password) <= 128:
        raise LocalQaAccountError("A senha precisa ter de 12 a 128 caracteres.")
    if db.exec(select(User).where(User.email == normalized)).first() is not None:
        raise LocalQaAccountError("Já existe uma conta com esse e-mail.")

    linked = None
    if role in (Role.MEDICO, Role.PACIENTE):
        if isinstance(linked_id, bool) or not isinstance(linked_id, int) or linked_id < 1:
            raise LocalQaAccountError(
                "Informe o ID de um cadastro existente sem conta vinculada."
            )
        model = Professional if role is Role.MEDICO else Patient
        linked = db.exec(
            select(model).where(model.id == linked_id).with_for_update()
        ).first()
        if linked is None:
            raise LocalQaAccountError("Cadastro não encontrado.")
        if linked.user_id is not None:
            raise LocalQaAccountError("O cadastro já está vinculado a uma conta.")
        if role is Role.MEDICO and not linked.is_active:
            raise LocalQaAccountError("O profissional está inativo.")
        if role is Role.PACIENTE and not patient_consent_confirmed:
            raise LocalQaAccountError("Confirme o consentimento do paciente.")
    elif linked_id is not None:
        raise LocalQaAccountError("Este perfil não aceita vínculo clínico.")

    user = User(
        email=normalized,
        password_hash=hash_password(password),
        role=role.value,
    )
    try:
        db.add(user)
        db.flush()
        if linked is not None:
            linked.user_id = user.id
            db.add(linked)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise LocalQaAccountError(
            "E-mail ou vínculo já utilizado por outra conta."
        ) from exc

    db.refresh(user)
    return user


def _choose_role() -> Role:
    roles = tuple(Role)
    print("\nPerfil da nova conta:")
    for index, role in enumerate(roles, start=1):
        print(f"  {index}. {role.label}")
    selected = input("Número do perfil: ").strip()
    if not selected.isdecimal() or not 1 <= int(selected) <= len(roles):
        raise LocalQaAccountError("Selecione um número de perfil válido.")
    return roles[int(selected) - 1]


def main() -> int:
    if not sys.stdin.isatty():
        print("Abra um terminal interativo para usar make user.", file=sys.stderr)
        return 2

    try:
        require_isolated_local_database()
        print("Vitta One — criar usuário no banco QA local (não produção)")
        role = _choose_role()
        email = input("E-mail: ").strip()
        linked_id = None
        consent = False
        if role in (Role.MEDICO, Role.PACIENTE):
            entity = "profissional" if role is Role.MEDICO else "paciente"
            print(f"Cadastre o {entity} pela aplicação antes de vinculá-lo.")
            raw_id = input(f"ID do {entity} sem acesso: ").strip()
            if not raw_id.isdecimal() or int(raw_id) < 1:
                raise LocalQaAccountError("ID inválido.")
            linked_id = int(raw_id)
            if role is Role.PACIENTE:
                consent = (
                    input("Consentimento do paciente confirmado? [s/N]: ")
                    .strip()
                    .casefold()
                    in {"s", "sim"}
                )
        password = getpass("Senha (12 a 128 caracteres): ")
        confirmation = getpass("Confirme a senha: ")
        if password != confirmation:
            raise LocalQaAccountError("As senhas não conferem.")

        with rx.session() as db:
            user = create_local_user(
                db,
                email=email,
                password=password,
                role=role,
                linked_id=linked_id,
                patient_consent_confirmed=consent,
            )
        print(f"Conta criada: {user.email} — {role.label} (ID {user.id}).")
        print("Acesse http://localhost:3000/login.")
        return 0
    except (LocalQaAccountError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, LocalQaAccountError):
            print(f"Criação recusada: {exc}", file=sys.stderr)
        else:
            print("\nCriação cancelada.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
