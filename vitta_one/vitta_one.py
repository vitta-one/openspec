"""Vitta-One Reflex application entry point."""

import reflex as rx

from rxconfig import config
from vitta_one.models import AuthSession, User

# Keep persistent models imported from the application module so Reflex/Alembic
# can discover their metadata when generating migrations.
_AUTH_MODELS = (User, AuthSession)


class State(rx.State):
    """Base application state."""


def index() -> rx.Component:
    """Render the default Reflex bootstrap page."""
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Welcome to Reflex!", size="9"),
            rx.text(
                "Get started by editing ",
                rx.code(f"{config.app_name}/{config.app_name}.py"),
                size="5",
            ),
            rx.link(
                rx.button("Check out our docs!"),
                href="https://reflex.dev/docs/getting-started/introduction/",
                is_external=True,
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index)
