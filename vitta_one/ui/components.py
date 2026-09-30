"""Shared Vitta-One product UI components for authentication and protected shells."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState


def brand_mark() -> rx.Component:
    """Render the compact Vitta-One identity mark."""
    return rx.box(
        rx.text("V1", font_weight="800", letter_spacing="-0.04em"),
        width="2.75rem",
        height="2.75rem",
        display="flex",
        align_items="center",
        justify_content="center",
        border_radius="0.9rem 0.9rem 0.9rem 0.3rem",
        background="var(--vitta-primary)",
        color="var(--vitta-surface)",
        box_shadow="var(--vitta-shadow-mark)",
        aria_hidden="true",
    )


def loading_surface(message: str = "Verificando acesso…") -> rx.Component:
    """Render a stable neutral loading surface without exposing protected content."""
    return rx.center(
        rx.vstack(
            brand_mark(),
            rx.spinner(size="3"),
            rx.text(message, color="var(--vitta-text-muted)", size="2"),
            spacing="4",
            align="center",
        ),
        width="100%",
        min_height="100dvh",
        padding="1.5rem",
        background="var(--vitta-canvas)",
        role="status",
        aria_live="polite",
    )


def error_banner(message, element_id: str | None = None) -> rx.Component:
    """Render an accessible inline error region."""
    id_props = {"id": element_id} if element_id else {}
    return rx.box(
        rx.text(message, size="2", line_height="1.5"),
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-danger-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-danger-soft)",
        color="var(--vitta-danger)",
        role="alert",
        aria_live="assertive",
        **id_props,
    )


def login_form() -> rx.Component:
    """Render the public login form without exposing account creation."""
    return rx.el.form(
        rx.vstack(
            rx.box(
                rx.el.label(
                    "E-mail",
                    html_for="login-email",
                    font_weight="650",
                    font_size="0.9rem",
                    color="var(--vitta-text)",
                ),
                rx.el.input(
                    id="login-email",
                    name="email",
                    type="email",
                    required=True,
                    max_length=320,
                    auto_complete="username",
                    input_mode="email",
                    class_name="vitta-input",
                    margin_top="0.45rem",
                    aria_invalid=AuthState.login_error != "",
                    aria_describedby=rx.cond(
                        AuthState.login_error != "", "login-error", ""
                    ),
                ),
                width="100%",
            ),
            rx.box(
                rx.el.label(
                    "Senha",
                    html_for="login-password",
                    font_weight="650",
                    font_size="0.9rem",
                    color="var(--vitta-text)",
                ),
                rx.box(
                    rx.el.input(
                        id="login-password",
                        name="password",
                        type=rx.cond(AuthState.show_password, "text", "password"),
                        required=True,
                        auto_complete="current-password",
                        class_name="vitta-input vitta-password-input",
                        aria_invalid=AuthState.login_error != "",
                        aria_describedby=rx.cond(
                            AuthState.login_error != "", "login-error", ""
                        ),
                    ),
                    rx.button(
                        rx.cond(AuthState.show_password, "Ocultar", "Mostrar"),
                        type="button",
                        variant="ghost",
                        size="2",
                        color_scheme="teal",
                        class_name="vitta-password-toggle",
                        on_click=AuthState.toggle_password_visibility,
                        aria_label=rx.cond(
                            AuthState.show_password,
                            "Ocultar senha",
                            "Mostrar senha",
                        ),
                    ),
                    position="relative",
                    margin_top="0.45rem",
                ),
                width="100%",
            ),
            rx.cond(
                AuthState.login_error != "",
                error_banner(AuthState.login_error, "login-error"),
                rx.fragment(),
            ),
            rx.button(
                "Entrar",
                type="submit",
                size="3",
                width="100%",
                min_height="3rem",
                color_scheme="teal",
                high_contrast=True,
                loading=AuthState.is_submitting,
                disabled=AuthState.is_submitting,
                class_name="vitta-primary-action",
            ),
            rx.text(
                "Não há cadastro público. O acesso é criado pela administração da clínica.",
                color="var(--vitta-text-muted)",
                font_size="0.78rem",
                line_height="1.5",
                text_align="center",
            ),
            spacing="4",
            width="100%",
        ),
        on_submit=AuthState.login,
        width="100%",
    )


def authenticated_header() -> rx.Component:
    """Render the shared protected-shell header."""
    return rx.flex(
        rx.hstack(
            brand_mark(),
            rx.vstack(
                rx.heading("Vitta-One", size="5", color="var(--vitta-text)"),
                rx.text("Ambiente interno da clínica", size="1", color="var(--vitta-text-muted)"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        rx.hstack(
            rx.vstack(
                rx.text(AuthState.current_email, size="2", font_weight="600"),
                rx.text(AuthState.role_label, size="1", color="var(--vitta-text-muted)"),
                spacing="0",
                align=rx.breakpoints(initial="start", sm="end"),
            ),
            rx.button(
                "Sair",
                variant="outline",
                color_scheme="teal",
                size="2",
                on_click=AuthState.logout,
            ),
            spacing="3",
            align="center",
        ),
        width="100%",
        direction=rx.breakpoints(initial="column", sm="row"),
        align=rx.breakpoints(initial="stretch", sm="center"),
        justify="between",
        gap="1rem",
        padding="1rem 0",
        border_bottom="1px solid var(--vitta-border)",
    )


def dashboard_shell(role: Role, title: str, description: str) -> rx.Component:
    """Render a minimal protected dashboard shell for one domain role."""
    protected_content = rx.box(
        authenticated_header(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        width="0.55rem",
                        height="0.55rem",
                        border_radius="999px",
                        background="var(--vitta-primary)",
                        aria_hidden="true",
                    ),
                    rx.text("Acesso autorizado", color="var(--vitta-primary)", font_weight="700", size="2"),
                    spacing="2",
                    align="center",
                ),
                rx.heading(title, size="8", letter_spacing="-0.03em", max_width="18ch"),
                rx.text(
                    description,
                    color="var(--vitta-text-muted)",
                    max_width="62ch",
                    line_height="1.7",
                ),
                rx.box(
                    rx.text(
                        "Este painel é apenas o shell de autenticação e autorização. Funcionalidades de negócio serão adicionadas por changes específicas do OpenSpec.",
                        line_height="1.6",
                        color="var(--vitta-text-muted)",
                    ),
                    width="100%",
                    padding=rx.breakpoints(initial="1rem", sm="1.25rem"),
                    border="1px solid var(--vitta-border)",
                    border_radius="var(--vitta-radius-panel)",
                    background="var(--vitta-surface-muted)",
                ),
                rx.cond(
                    AuthState.shell_error != "",
                    error_banner(AuthState.shell_error),
                    rx.fragment(),
                ),
                spacing="5",
                align="start",
                width="100%",
            ),
            padding=rx.breakpoints(initial="2rem 0", sm="3.5rem 0"),
        ),
        width="100%",
        max_width="72rem",
        margin="0 auto",
        padding="0 1.25rem",
    )

    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == role.value)
        & (AuthState.verified_path == role.dashboard_path),
        protected_content,
        loading_surface(),
    )


def protected_workspace(role: Role, *children: rx.Component) -> rx.Component:
    """Render an authorized operational workspace using the shared product shell."""
    protected_content = rx.box(
        authenticated_header(),
        rx.box(
            rx.vstack(
                *children,
                spacing="5",
                align="stretch",
                width="100%",
            ),
            padding=rx.breakpoints(initial="1.5rem 0 2.5rem", sm="2.25rem 0 3.5rem"),
        ),
        width="100%",
        max_width="72rem",
        margin="0 auto",
        padding="0 1.25rem",
    )

    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == role.value)
        & (AuthState.verified_path == role.dashboard_path),
        protected_content,
        loading_surface(),
    )


def section_panel(*children, **props) -> rx.Component:
    """Render a quiet operational section using the established Vitta-One surface."""
    return rx.box(
        *children,
        width="100%",
        padding=rx.breakpoints(initial="1rem", sm="1.35rem"),
        background="var(--vitta-surface)",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-panel)",
        **props,
    )


def success_banner(message) -> rx.Component:
    """Render an accessible inline success region."""
    return rx.box(
        rx.text(message, size="2", line_height="1.5"),
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-success-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-success-soft)",
        color="var(--vitta-success)",
        role="status",
        aria_live="polite",
    )


def feedback_region(error, success, element_id: str = "page-feedback") -> rx.Component:
    """Render the canonical page-level error/success feedback region."""
    return rx.box(
        rx.cond(error != "", error_banner(error, element_id), rx.fragment()),
        rx.cond(success != "", success_banner(success), rx.fragment()),
        width="100%",
    )


def field_label(text: str, control_id: str) -> rx.Component:
    """Render the canonical label styling for operational forms."""
    return rx.el.label(
        text,
        html_for=control_id,
        font_weight="650",
        font_size="0.9rem",
        color="var(--vitta-text)",
    )
