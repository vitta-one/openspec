"""Manual bootstrap entry point for the first Vitta-One Administrator."""

import os

import reflex as rx

from vitta_one.auth.service import BootstrapConflictError, bootstrap_first_admin

_EMAIL_ENV = "VITTA_ONE_BOOTSTRAP_ADMIN_EMAIL"
_PASSWORD_ENV = "VITTA_ONE_BOOTSTRAP_ADMIN_PASSWORD"


def main() -> int:
    """Create the first administrator from environment-provided credentials."""
    email = os.getenv(_EMAIL_ENV, "").strip()
    password = os.getenv(_PASSWORD_ENV, "")

    missing = [
        name
        for name, value in ((_EMAIL_ENV, email), (_PASSWORD_ENV, password))
        if not value
    ]
    if missing:
        print(f"Defina as variáveis obrigatórias: {', '.join(missing)}.")
        return 2

    try:
        with rx.session() as db:
            result = bootstrap_first_admin(db, email=email, password=password)
    except (BootstrapConflictError, ValueError) as exc:
        print(f"Bootstrap recusado: {exc}")
        return 3

    if result.created:
        print("Administrador inicial criado.")
    else:
        print("Bootstrap já concluído; administrador existente preservado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
