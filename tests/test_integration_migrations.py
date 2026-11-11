"""Reviewed migration functions preserve the existing schema on an isolated database."""
import importlib.util
import os
from pathlib import Path
from uuid import uuid4
import pytest

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine
import vitta_one.models


@pytest.mark.parametrize("database", ["sqlite", "postgresql"])
def test_additive_migrations_upgrade_and_downgrade_without_clinical_changes(database):
    def load(name):
        spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / "alembic" / "versions" / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    financial = load("f031a5aa5001_add_asaas_financial")
    notifications = load("f031a5aa5002_add_transactional_notifications")
    added = {name for name in SQLModel.metadata.tables if name.startswith(("financial_", "email_", "notification_"))}
    schema = None
    if database == "postgresql":
        url = os.getenv("DATABASE_URL", "")
        if not url.startswith("postgresql") or os.getenv("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes":
            pytest.skip("PostgreSQL migration tests require an explicitly disposable database.")
        schema = "vitta_migrations_" + uuid4().hex
        admin_engine = create_engine(url)
        with admin_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine, tables=[t for n,t in SQLModel.metadata.tables.items() if n not in added])
    with engine.begin() as conn:
        baseline = set(inspect(conn).get_table_names())
        with Operations.context(MigrationContext.configure(conn)):
            financial.upgrade()
            notifications.upgrade()
            inspector = inspect(conn)
            assert set(inspector.get_table_names()) == baseline | added
            for name in added:
                assert {c["name"] for c in inspector.get_columns(name)} == set(SQLModel.metadata.tables[name].columns.keys())
            notifications.downgrade()
            financial.downgrade()
        assert set(inspect(conn).get_table_names()) == baseline
    engine.dispose()
    if schema:
        with admin_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()
