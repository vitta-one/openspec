"""Add missing synthetic roles for screenshots on disposable CI PostgreSQL only.

The existing prescription QA seed supplies Administrador, Recepcionista, Médico,
appointments and prescriptions. This seed adds Paciente, Financeiro and the
medical first-access state without creating invitations or sending any e-mail.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine, select

from vitta_one.auth.roles import Role
from vitta_one.auth.security import hash_password
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient


def main() -> None:
    if os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes":
        raise RuntimeError("A criação de contas QA exige banco descartável")
    url = make_url(os.environ["DATABASE_URL"])
    if (url.drivername != "postgresql+psycopg" or url.host not in ("localhost", "127.0.0.1")
            or url.port != 5432 or url.database != "vitta_one" or url.username != "postgres"):
        raise RuntimeError("O banco não corresponde ao PostgreSQL isolado do GitHub Actions")

    fixture_file = Path("qa-artifacts/fixture.json")
    fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
    password = os.environ["VITTA_ONE_QA_PASSWORD"]

    with Session(create_engine(os.environ["DATABASE_URL"])) as db:
        patient = db.exec(select(Patient).where(Patient.name == fixture["patient_name"])).one()
        if patient.user_id is not None:
            raise RuntimeError("Paciente QA já possui identidade; seed não será sobrescrito")
        emails = {
            "patient_portal_email": "qa-portal-paciente@example.invalid",
            "finance_email": "qa-financeiro@example.invalid",
            "first_access_email": "qa-primeiro-acesso@example.invalid",
        }
        identities = [
            User(email=emails["patient_portal_email"], role=Role.PACIENTE.value,
                 password_hash=hash_password(password)),
            User(email=emails["finance_email"], role=Role.FINANCEIRO.value,
                 password_hash=hash_password(password)),
            User(email=emails["first_access_email"], role=Role.MEDICO.value,
                 password_hash=hash_password(password), must_change_password=True,
                 temporary_password_expires_at=datetime.now(timezone.utc) + timedelta(hours=2)),
        ]
        for identity in identities:
            db.add(identity)
        db.flush()
        patient.user_id = identities[0].id
        db.add(patient)
        db.commit()
        fixture.update(emails)

    fixture_file.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
    print("Identidades adicionais de QA criadas no banco descartável (sem convites ou e-mails)")


if __name__ == "__main__":
    main()
