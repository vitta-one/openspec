"""Shared Vitta-One product UI components for authentication and protected shells."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState


def brand_mark(*, decorative: bool = False) -> rx.Component:
    """Render the compact official Vitta-One mark derived from the supplied logo."""
    aria_props = {"aria_hidden": "true"} if decorative else {}
    return rx.image(
        src="/vitta-one-mark.webp",
        alt="" if decorative else "Vitta-One",
        width="2.9rem",
        height="2.9rem",
        object_fit="contain",
        display="block",
        border_radius="0.9rem",
        box_shadow="var(--vitta-shadow-mark)",
        **aria_props,
    )


def brand_logo(*, width: str = "11rem") -> rx.Component:
    """Render the official horizontal Vitta-One logo supplied for this project."""
    return rx.image(
        src="/vitta-one-logo.webp",
        alt="Vitta-One",
        width=width,
        height="auto",
        object_fit="contain",
        display="block",
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
        rx.hstack(
            rx.icon("circle_alert", size=17, aria_hidden="true"),
            rx.text(message, size="2", line_height="1.5"),
            spacing="2",
            align="start",
        ),
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
                    font_weight="700",
                    font_size="0.88rem",
                    color="var(--vitta-text)",
                ),
                rx.el.input(
                    id="login-email",
                    name="email",
                    type="email",
                    required=True,
                    max_length=320,
                    auto_complete="username",
                    auto_capitalize="none",
                    spell_check=False,
                    input_mode="email",
                    enter_key_hint="next",
                    placeholder="seu.email@clinica.com.br",
                    class_name="vitta-input vitta-login-input",
                    margin_top="0.5rem",
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
                    font_weight="700",
                    font_size="0.88rem",
                    color="var(--vitta-text)",
                ),
                rx.box(
                    rx.el.input(
                        id="login-password",
                        name="password",
                        type=rx.cond(AuthState.show_password, "text", "password"),
                        required=True,
                        auto_complete="current-password",
                        spell_check=False,
                        enter_key_hint="go",
                        placeholder="Digite sua senha",
                        class_name="vitta-input vitta-login-input vitta-password-input",
                        aria_invalid=AuthState.login_error != "",
                        aria_describedby=rx.cond(
                            AuthState.login_error != "", "login-error", ""
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            AuthState.show_password,
                            rx.icon("eye_off", size=20),
                            rx.icon("eye", size=20),
                        ),
                        type="button",
                        variant="ghost",
                        color_scheme="teal",
                        class_name="vitta-password-toggle",
                        on_click=AuthState.toggle_password_visibility,
                        aria_label=rx.cond(
                            AuthState.show_password,
                            "Ocultar senha",
                            "Mostrar senha",
                        ),
                        aria_pressed=AuthState.show_password,
                    ),
                    position="relative",
                    margin_top="0.5rem",
                ),
                width="100%",
            ),
            rx.box(
                rx.cond(
                    AuthState.login_error != "",
                    error_banner(AuthState.login_error, "login-error"),
                    rx.box(min_height="0.25rem"),
                ),
                width="100%",
                min_height=rx.cond(AuthState.login_error != "", "auto", "0.25rem"),
            ),
            rx.button(
                rx.hstack(
                    rx.cond(
                        AuthState.is_submitting,
                        rx.spinner(size="2"),
                        rx.icon("log_in", size=18),
                    ),
                    rx.text(
                        rx.cond(
                            AuthState.is_submitting,
                            "Validando acesso…",
                            "Entrar no Vitta-One",
                        ),
                        font_weight="750",
                    ),
                    spacing="2",
                    align="center",
                ),
                type="submit",
                size="3",
                width="100%",
                min_height="3.15rem",
                color_scheme="teal",
                high_contrast=True,
                disabled=AuthState.is_submitting,
                class_name="vitta-primary-action",
            ),
            rx.hstack(
                rx.icon("shield_check", size=16, color="var(--vitta-primary)"),
                rx.text(
                    "Acesso restrito à equipe autorizada pela clínica.",
                    color="var(--vitta-text-muted)",
                    font_size="0.76rem",
                    line_height="1.45",
                ),
                spacing="2",
                align="start",
                width="100%",
                justify="center",
            ),
            spacing="4",
            width="100%",
        ),
        on_submit=AuthState.login,
        no_validate=True,
        width="100%",
    )


def authenticated_header() -> rx.Component:
    """Render the shared protected-shell header."""
    return rx.flex(
        rx.hstack(
            brand_mark(decorative=True),
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


def protected_admin_surface(child: rx.Component) -> rx.Component:
    """Render the dedicated administrator shell after exact server-side role verification."""
    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == Role.ADMINISTRADOR.value)
        & (AuthState.verified_path == Role.ADMINISTRADOR.dashboard_path),
        child,
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
        rx.hstack(
            rx.icon("circle_check", size=17, aria_hidden="true"),
            rx.text(message, size="2", line_height="1.5"),
            spacing="2",
            align="start",
        ),
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
