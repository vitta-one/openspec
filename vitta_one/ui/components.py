"""Shared Vitta-One product UI components for authentication and protected shells."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState


_ADMIN_NAV = (
    ("Visão geral", "layout_dashboard", "/admin", "overview"),
    ("Recepção", "clipboard_list", "/admin/recepcao", "reception"),
    ("Agenda", "calendar", "/admin/agenda", "agenda"),
    ("Atendimento clínico", "stethoscope", "/admin/atendimento", "clinical"),
    ("Pacientes", "users", "/admin/pacientes", "patients"),
    ("Financeiro", "wallet", "/admin/financeiro", "finance"),
    ("Administração", "settings", "/admin/administracao", "administration"),
)

_ROLE_NAV = {
    Role.RECEPCIONISTA: (("Recepção", "clipboard_list", "/recepcao", "reception"),),
    Role.MEDICO: (("Atendimento clínico", "stethoscope", "/medico", "clinical"),),
    Role.FINANCEIRO: (("Financeiro", "wallet", "/financeiro", "finance"),),
}


def brand_logo(*, compact: bool = False) -> rx.Component:
    """Render the supplied Vitta-One identity asset."""
    return rx.image(
        src="/vitta-one-logo.png",
        alt="Vitta-One",
        width="2.65rem" if compact else "10.75rem",
        height="auto",
        object_fit="contain",
        class_name="vitta-brand-logo",
    )


def brand_mark() -> rx.Component:
    """Render a compact brand mark for constrained loading states."""
    return rx.box(
        rx.icon("plus", size=24, stroke_width=3),
        width="2.75rem",
        height="2.75rem",
        display="flex",
        align_items="center",
        justify_content="center",
        border_radius="999px",
        border="3px solid var(--vitta-primary)",
        color="var(--vitta-primary)",
        background="var(--vitta-surface)",
        aria_hidden="true",
    )


def loading_surface(message: str = "Verificando acesso…") -> rx.Component:
    """Render a stable neutral loading surface without exposing protected content."""
    return rx.center(
        rx.vstack(
            brand_logo(),
            rx.spinner(size="3", color="var(--vitta-primary)"),
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
    return rx.flex(
        rx.icon("circle_alert", size=18, flex_shrink="0"),
        rx.text(message, size="2", line_height="1.5"),
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-danger-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-danger-soft)",
        color="var(--vitta-danger)",
        role="alert",
        aria_live="assertive",
        gap="0.65rem",
        align="start",
        **id_props,
    )


def login_form() -> rx.Component:
    """Render the public login form without exposing account creation."""
    password_label = rx.cond(
        AuthState.show_password,
        "Ocultar senha",
        "Mostrar senha",
    )
    password_icon = rx.cond(
        AuthState.show_password,
        rx.icon("eye_off", size=19),
        rx.icon("eye", size=19),
    )

    return rx.el.form(
        rx.vstack(
            rx.box(
                field_label("E-mail", "login-email"),
                rx.box(
                    rx.icon("mail", size=18, class_name="vitta-field-leading-icon"),
                    rx.el.input(
                        id="login-email",
                        name="email",
                        type="email",
                        max_length=320,
                        auto_complete="username",
                        input_mode="email",
                        placeholder="nome@clinica.com.br",
                        class_name="vitta-input vitta-input-leading",
                        aria_invalid=AuthState.login_error != "",
                        aria_describedby=rx.cond(
                            AuthState.login_error != "", "login-error", ""
                        ),
                    ),
                    class_name="vitta-field-wrap",
                ),
                width="100%",
            ),
            rx.box(
                rx.flex(
                    field_label("Senha", "login-password"),
                    rx.text(
                        "Acesso interno",
                        size="1",
                        color="var(--vitta-text-subtle)",
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                ),
                rx.box(
                    rx.icon("lock_keyhole", size=18, class_name="vitta-field-leading-icon"),
                    rx.el.input(
                        id="login-password",
                        name="password",
                        type=rx.cond(AuthState.show_password, "text", "password"),
                        auto_complete="current-password",
                        placeholder="Digite sua senha",
                        class_name="vitta-input vitta-input-leading vitta-password-input",
                        aria_invalid=AuthState.login_error != "",
                        aria_describedby=rx.cond(
                            AuthState.login_error != "", "login-error", ""
                        ),
                    ),
                    rx.button(
                        password_icon,
                        type="button",
                        variant="ghost",
                        class_name="vitta-password-toggle",
                        on_click=AuthState.toggle_password_visibility,
                        aria_label=password_label,
                        title=password_label,
                    ),
                    class_name="vitta-field-wrap",
                ),
                width="100%",
            ),
            rx.cond(
                AuthState.login_error != "",
                error_banner(AuthState.login_error, "login-error"),
                rx.fragment(),
            ),
            rx.button(
                rx.cond(
                    AuthState.is_submitting,
                    rx.hstack(rx.spinner(size="2"), rx.text("Entrando…"), spacing="2"),
                    rx.hstack(rx.text("Entrar"), rx.icon("arrow_right", size=18), spacing="2"),
                ),
                type="submit",
                width="100%",
                min_height="3.15rem",
                disabled=AuthState.is_submitting,
                class_name="vitta-primary-action",
            ),
            rx.flex(
                rx.icon("shield_check", size=16, color="var(--vitta-primary)"),
                rx.text(
                    "A sessão é validada no servidor. Não há cadastro público.",
                    color="var(--vitta-text-muted)",
                    font_size="0.78rem",
                    line_height="1.5",
                ),
                gap="0.5rem",
                align="start",
            ),
            spacing="4",
            width="100%",
        ),
        on_submit=AuthState.login,
        no_validate=True,
        width="100%",
    )


def _nav_item(label: str, icon: str, href: str, key: str, active_nav: str) -> rx.Component:
    is_active = key == active_nav
    return rx.link(
        rx.flex(
            rx.icon(icon, size=19, stroke_width=2),
            rx.text(label, size="2", font_weight="600" if is_active else "500"),
            gap="0.8rem",
            align="center",
            width="100%",
        ),
        href=href,
        class_name="vitta-nav-item vitta-nav-item-active" if is_active else "vitta-nav-item",
        aria_current="page" if is_active else None,
        underline="none",
    )


def app_sidebar(role: Role, active_nav: str) -> rx.Component:
    """Render the canonical product navigation for the current role."""
    nav_items = _ADMIN_NAV if role == Role.ADMINISTRADOR else _ROLE_NAV.get(role, ())
    return rx.box(
        rx.flex(
            rx.box(
                brand_logo(),
                padding="1.35rem 1.25rem 1.05rem",
                class_name="vitta-sidebar-brand",
            ),
            rx.box(
                rx.text(
                    "NAVEGAÇÃO",
                    class_name="vitta-sidebar-caption",
                ),
                rx.vstack(
                    *[
                        _nav_item(label, icon, href, key, active_nav)
                        for label, icon, href, key in nav_items
                    ],
                    spacing="1",
                    align="stretch",
                    width="100%",
                ),
                padding="0.8rem",
                flex="1",
                width="100%",
            ),
            rx.box(
                rx.flex(
                    rx.box(
                        rx.icon("user", size=17),
                        class_name="vitta-user-avatar",
                    ),
                    rx.box(
                        rx.text(AuthState.current_email, size="1", font_weight="650", class_name="vitta-ellipsis"),
                        rx.text(AuthState.role_label, size="1", color="var(--vitta-text-muted)"),
                        min_width="0",
                        flex="1",
                    ),
                    rx.button(
                        rx.icon("log_out", size=17),
                        type="button",
                        variant="ghost",
                        on_click=AuthState.logout,
                        aria_label="Sair do Vitta-One",
                        title="Sair",
                        class_name="vitta-icon-button",
                    ),
                    gap="0.65rem",
                    align="center",
                    width="100%",
                ),
                class_name="vitta-sidebar-user",
            ),
            direction="column",
            height="100%",
            width="100%",
        ),
        class_name="vitta-sidebar",
    )


def app_topbar(page_title: str) -> rx.Component:
    """Render compact context and session controls above each workspace."""
    return rx.flex(
        rx.box(
            rx.text(page_title, class_name="vitta-topbar-title"),
            rx.flex(
                rx.box(class_name="vitta-status-dot"),
                rx.text("Sistema operacional", size="1", color="var(--vitta-text-muted)"),
                gap="0.4rem",
                align="center",
                margin_top="0.18rem",
            ),
        ),
        rx.flex(
            rx.box(
                rx.icon("map_pin", size=15, color="var(--vitta-primary)"),
                rx.text("Ambiente local", size="1", color="var(--vitta-text-muted)"),
                class_name="vitta-context-chip",
            ),
            gap="0.65rem",
            align="center",
        ),
        class_name="vitta-topbar",
        justify="between",
        align="center",
        width="100%",
    )


def dashboard_shell(
    role: Role,
    title: str,
    description: str,
    *,
    active_nav: str,
    required_path: str | None = None,
) -> rx.Component:
    """Render a protected module shell when business functionality is not implemented yet."""
    return protected_workspace(
        role,
        module_empty_state(title, description),
        active_nav=active_nav,
        page_title=title,
        required_path=required_path,
    )


def protected_workspace(
    role: Role,
    *children: rx.Component,
    active_nav: str,
    page_title: str,
    required_path: str | None = None,
) -> rx.Component:
    """Render an authorized workspace using the canonical premium product shell."""
    expected_path = required_path or role.dashboard_path
    protected_content = rx.box(
        app_sidebar(role, active_nav),
        rx.box(
            app_topbar(page_title),
            rx.box(
                rx.vstack(
                    *children,
                    spacing="5",
                    align="stretch",
                    width="100%",
                ),
                class_name="vitta-page-content",
            ),
            class_name="vitta-app-main",
        ),
        class_name="vitta-app-frame",
    )

    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == role.value)
        & (AuthState.verified_path == expected_path),
        protected_content,
        loading_surface(),
    )


def page_heading(eyebrow: str, title: str, description: str) -> rx.Component:
    return rx.box(
        rx.text(eyebrow, class_name="vitta-eyebrow"),
        rx.heading(title, class_name="vitta-page-title"),
        rx.text(description, class_name="vitta-page-description"),
        width="100%",
    )


def section_panel(*children, **props) -> rx.Component:
    """Render the canonical operational surface."""
    extra_class = props.pop("class_name", "")
    return rx.box(
        *children,
        class_name=f"vitta-panel {extra_class}".strip(),
        **props,
    )


def module_empty_state(title: str, description: str) -> rx.Component:
    """Render an honest module state without fabricated operational data."""
    return section_panel(
        rx.center(
            rx.vstack(
                rx.box(
                    rx.icon("construction", size=24),
                    class_name="vitta-empty-icon",
                ),
                rx.heading(title, size="5", text_align="center"),
                rx.text(
                    description,
                    color="var(--vitta-text-muted)",
                    text_align="center",
                    max_width="56ch",
                    line_height="1.6",
                ),
                rx.badge("Módulo ainda não aplicado", variant="soft", color_scheme="gray"),
                spacing="3",
                align="center",
            ),
            min_height="18rem",
            width="100%",
        )
    )


def success_banner(message) -> rx.Component:
    """Render an accessible inline success region."""
    return rx.flex(
        rx.icon("circle_check", size=18, flex_shrink="0"),
        rx.text(message, size="2", line_height="1.5"),
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-success-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-success-soft)",
        color="var(--vitta-success)",
        role="status",
        aria_live="polite",
        gap="0.65rem",
        align="start",
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
        class_name="vitta-field-label",
    )
