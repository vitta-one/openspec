"""Reflex configuration for Vitta-One."""

import os

import reflex as rx


def _database_url() -> str:
    """Return the PostgreSQL URL required by the application."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL deve ser definida com uma URL PostgreSQL antes de iniciar o Vitta-One."
        )
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    raise RuntimeError("DATABASE_URL deve apontar para PostgreSQL.")


config = rx.Config(
    app_name="vitta_one",
    db_url=_database_url(),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
)
