"""Shared Vitta-One product UI components for authentication and protected shells."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.state import ReceptionQueueState


_NAV_BY_ROLE = {
    Role.RECEPCIONISTA: (
        ("Recepção", "/recepcao", "layout_dashboard", "recepcao"),
        ("Agenda", "/recepcao/agenda", "calendar_days", "agenda"),
        ("Pacientes", "/recepcao/pacientes", "users", "pacientes"),
        ("Fila de espera", "/recepcao/fila", "list_ordered", "fila"),
    ),
    Role.MEDICO: (
        ("Atendimento clínico", "/medico", "stethoscope", "atendimento"),
        ("Agenda", "/medico/agenda", "calendar_days", "agenda-medica"),
        ("Pacientes", "/medico/pacientes", "users", "pacientes-medico"),
    ),
    Role.PACIENTE: (
        ("Minhas consultas", "/paciente", "calendar_days", "consultas-paciente"),
        ("Agendar consulta", "/paciente/agendar", "calendar_plus", "agendar-paciente"),
    ),
    Role.FINANCEIRO: (
        ("Financeiro", "/financeiro", "wallet", "financeiro"),
    ),
}

_ADMIN_PREVIEW_NAV = (
    ("Recepção", "/admin/recepcao", "users", "recepcao"),
    ("Agenda", "/admin/agenda", "calendar", "agenda"),
    ("Atendimento clínico", "/admin/atendimento", "stethoscope", "atendimento"),
    ("Pacientes", "/admin/pacientes", "user", "pacientes"),
    ("Financeiro", "/admin/financeiro", "wallet", "financeiro"),
    ("Administração", "/admin", "settings", "administracao"),
)


def brand_logo(*, width: str = "9rem") -> rx.Component:
    """Render the official project logo supplied for Vitta-One."""
    return rx.image(
        src="/vitta-one-logo.png",
        alt="Vitta-One",
        width=width,
        height="auto",
        object_fit="contain",
        display="block",
    )


def brand_mark() -> rx.Component:
    """Backward-compatible compact brand surface for neutral loading states."""
    return rx.box(
        brand_logo(width="7.25rem"),
        padding="0.65rem 0.8rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-panel)",
        background="var(--vitta-surface)",
        box_shadow="var(--vitta-shadow-xs)",
    )


def loading_surface(message: str = "Verificando acesso…") -> rx.Component:
    """Render a stable neutral loading surface without exposing protected content."""
    return rx.center(
        rx.vstack(
            brand_mark(),
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
    return rx.box(
        rx.hstack(
            rx.icon("triangle_alert", size=17, flex_shrink="0"),
            rx.text(message, size="2", line_height="1.5"),
            spacing="2",
            align="start",
        ),
        width="100%",
        padding="0.85rem 0.95rem",
        border="1px solid var(--vitta-danger-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-danger-soft)",
        color="var(--vitta-danger)",
        role="alert",
        aria_live="assertive",
        **id_props,
    )


def success_banner(message) -> rx.Component:
    """Render an accessible inline success region."""
    return rx.box(
        rx.hstack(
            rx.icon("circle_check", size=17, flex_shrink="0"),
            rx.text(message, size="2", line_height="1.5"),
            spacing="2",
            align="start",
        ),
        width="100%",
        padding="0.85rem 0.95rem",
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
        font_weight="700",
        font_size="0.86rem",
        color="var(--vitta-text)",
    )


def login_form() -> rx.Component:
    """Render the public login form with an accessible icon-only password reveal."""
    return rx.el.form(
        rx.vstack(
            rx.box(
                field_label("E-mail", "login-email"),
                rx.el.input(
                    id="login-email",
                    name="email",
                    type="email",
                    required=True,
                    max_length=320,
                    auto_complete="username",
                    input_mode="email",
                    class_name="vitta-input",
                    placeholder="seu.email@clinica.com",
                    margin_top="0.45rem",
                    aria_invalid=AuthState.login_error != "",
                    aria_describedby=rx.cond(
                        AuthState.login_error != "", "login-error", ""
                    ),
                ),
                width="100%",
            ),
            rx.box(
                field_label("Senha", "login-password"),
                rx.box(
                    rx.el.input(
                        id="login-password",
                        name="password",
                        type=rx.cond(AuthState.show_password, "text", "password"),
                        required=True,
                        auto_complete="current-password",
                        class_name="vitta-input vitta-password-input",
                        placeholder="Digite sua senha",
                        aria_invalid=AuthState.login_error != "",
                        aria_describedby=rx.cond(
                            AuthState.login_error != "", "login-error", ""
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            AuthState.show_password,
                            rx.icon("eye_off", size=19),
                            rx.icon("eye", size=19),
                        ),
                        type="button",
                        variant="ghost",
                        size="2",
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
                rx.hstack(
                    rx.cond(
                        AuthState.is_submitting,
                        rx.spinner(size="2"),
                        rx.icon("log_in", size=18),
                    ),
                    rx.text("Entrar"),
                    spacing="2",
                    align="center",
                    justify="center",
                ),
                type="submit",
                size="3",
                width="100%",
                min_height="3.1rem",
                color_scheme="teal",
                high_contrast=True,
                disabled=AuthState.is_submitting,
                class_name="vitta-primary-action",
            ),
            rx.hstack(
                rx.icon("shield_check", size=15),
                rx.text(
                    "Acesso restrito à equipe autorizada.",
                    font_size="0.78rem",
                    line_height="1.45",
                ),
                spacing="2",
                justify="center",
                align="center",
                color="var(--vitta-text-subtle)",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        on_submit=AuthState.login,
        no_validate=True,
        width="100%",
        class_name="vitta-login-form",
    )


def _nav_link(
    label: str,
    href: str,
    icon: str,
    *,
    active: bool,
) -> rx.Component:
    aria_props = {"aria_current": "page"} if active else {}
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=18, flex_shrink="0"),
            rx.text(label, white_space="nowrap"),
            spacing="3",
            align="center",
        ),
        href=href,
        class_name="vitta-nav-link",
        background=("var(--vitta-primary)" if active else "transparent"),
        color=("#ffffff" if active else "var(--vitta-text-muted)"),
        box_shadow=(
            "0 8px 18px rgba(15, 118, 110, 0.14)" if active else "none"
        ),
        **aria_props,
    )


def _admin_navigation(active: str) -> rx.Component:
    preview_items = rx.vstack(
        *[
            _nav_link(label, href, icon, active=key == active)
            for label, href, icon, key in _ADMIN_PREVIEW_NAV
        ],
        spacing="1",
        align="stretch",
        width="100%",
    )
    standard_items = rx.vstack(
        _nav_link(
            "Administração",
            "/admin",
            "settings",
            active=active == "administracao",
        ),
        spacing="1",
        align="stretch",
        width="100%",
    )
    return rx.cond(AuthState.local_admin_preview, preview_items, standard_items)


def _role_navigation(role: Role, active: str) -> rx.Component:
    if role is Role.ADMINISTRADOR:
        return _admin_navigation(active)

    items = _NAV_BY_ROLE.get(role, ())
    return rx.vstack(
        *[
            _nav_link(label, href, icon, active=key == active)
            for label, href, icon, key in items
        ],
        spacing="1",
        align="stretch",
        width="100%",
    )


def authenticated_sidebar(role: Role, active: str) -> rx.Component:
    """Render role-aware product navigation; local Admin preview is explicitly gated."""
    return rx.el.aside(
        rx.box(
            brand_logo(width="8.75rem"),
            class_name="vitta-sidebar-brand",
        ),
        rx.cond(
            (AuthState.current_role == Role.ADMINISTRADOR.value)
            & AuthState.local_admin_preview,
            rx.hstack(
                rx.icon("monitor_cog", size=14),
                rx.text("Modo local de QA", font_size="0.72rem", font_weight="750"),
                spacing="2",
                align="center",
                class_name="vitta-local-badge",
            ),
            rx.fragment(),
        ),
        rx.el.nav(
            _role_navigation(role, active),
            aria_label="Navegação principal",
            class_name="vitta-sidebar-nav",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("user", size=16),
                        class_name="vitta-session-avatar",
                    ),
                    rx.box(
                        rx.text(
                            AuthState.role_label,
                            font_size="0.78rem",
                            font_weight="750",
                            color="var(--vitta-text)",
                        ),
                        rx.text(
                            AuthState.current_email,
                            font_size="0.7rem",
                            color="var(--vitta-text-subtle)",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            white_space="nowrap",
                        ),
                        min_width="0",
                        flex="1",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("log_out", size=16),
                        rx.text("Sair"),
                        spacing="2",
                        align="center",
                    ),
                    type="button",
                    variant="ghost",
                    size="2",
                    color_scheme="gray",
                    width="100%",
                    justify_content="flex-start",
                    on_click=AuthState.logout,
                ),
                spacing="3",
                align="stretch",
                width="100%",
            ),
            class_name="vitta-sidebar-session",
        ),
        class_name=("vitta-sidebar vitta-sidebar--patient" if role is Role.PACIENTE else "vitta-sidebar"),
    )


def _reception_topbar_search() -> rx.Component:
    return rx.cond(
        AuthState.current_role == Role.RECEPCIONISTA.value,
        rx.el.form(
            rx.box(
                rx.icon(
                    "search",
                    size=16,
                    aria_hidden="true",
                    class_name="vitta-topbar-search-icon",
                ),
                rx.el.input(
                    id="topbar-patient-search",
                    name="query",
                    type="search",
                    value=ReceptionQueueState.quick_search_query,
                    on_change=ReceptionQueueState.update_quick_search_query,
                    placeholder="Buscar paciente, telefone ou CPF",
                    auto_complete="off",
                    max_length=100,
                    disabled=ReceptionQueueState.is_quick_searching,
                    aria_label="Buscar paciente por nome, telefone ou CPF",
                    aria_controls="topbar-patient-results",
                    aria_expanded=(ReceptionQueueState.quick_search_results.length() > 0)
                    | (ReceptionQueueState.quick_search_error != ""),
                    aria_autocomplete="list",
                    class_name="vitta-topbar-search-input",
                ),
                rx.button(
                    rx.icon("arrow_right", size=16),
                    type="submit",
                    variant="ghost",
                    size="2",
                    disabled=ReceptionQueueState.is_quick_searching,
                    loading=ReceptionQueueState.is_quick_searching,
                    aria_label="Buscar paciente",
                    class_name="vitta-topbar-search-submit",
                ),
                class_name="vitta-topbar-search-control",
            ),
            rx.cond(
                ReceptionQueueState.quick_search_results.length() > 0,
                rx.vstack(
                    rx.foreach(
                        ReceptionQueueState.quick_search_results,
                        lambda row: rx.button(
                            rx.vstack(
                                rx.text(row["name"], font_weight="700", size="2"),
                                rx.text(
                                    row["phone"],
                                    size="1",
                                    color="var(--vitta-text-muted)",
                                ),
                                align="start",
                                spacing="1",
                                width="100%",
                            ),
                            type="button",
                            variant="ghost",
                            on_click=ReceptionQueueState.select_quick_search_patient(
                                row["id"]
                            ),
                            aria_label="Selecionar paciente " + row["name"],
                            class_name="vitta-topbar-search-result",
                        ),
                    ),
                    id="topbar-patient-results",
                    role="region",
                    aria_label="Resultados da busca de pacientes",
                    align="stretch",
                    spacing="1",
                    class_name="vitta-topbar-search-results",
                ),
                rx.cond(
                    ReceptionQueueState.quick_search_error != "",
                    rx.box(
                        rx.text(
                            ReceptionQueueState.quick_search_error,
                            size="2",
                            role="status",
                            aria_live="polite",
                        ),
                        id="topbar-patient-results",
                        class_name="vitta-topbar-search-results vitta-topbar-search-feedback",
                    ),
                    rx.fragment(),
                ),
            ),
            on_submit=ReceptionQueueState.quick_search_patients,
            no_validate=True,
            class_name="vitta-topbar-search-form",
        ),
        rx.fragment(),
    )


def authenticated_topbar() -> rx.Component:
    """Render real shell controls and a receptionist-only persisted patient search."""
    return rx.el.header(
        _reception_topbar_search(),
        rx.hstack(
            rx.icon("layout_dashboard", size=16, color="var(--vitta-primary)"),
            rx.text(
                rx.cond(
                    AuthState.current_role == Role.RECEPCIONISTA.value,
                    "Vitta-One · Recepção",
                    "Sessão ativa",
                ),
                font_size="0.78rem",
                font_weight="700",
                color="var(--vitta-text-muted)",
                white_space="nowrap",
            ),
            spacing="2",
            align="center",
            class_name="vitta-topbar-system-status",
        ),
        rx.hstack(
            rx.text(
                AuthState.current_email,
                font_size="0.78rem",
                color="var(--vitta-text-subtle)",
                display=rx.breakpoints(initial="none", sm="block"),
            ),
            rx.badge(
                AuthState.role_label,
                variant="soft",
                color_scheme="teal",
                high_contrast=True,
            ),
            spacing="3",
            align="center",
            class_name="vitta-topbar-account",
        ),
        class_name="vitta-topbar",
    )


def page_header(
    eyebrow: str,
    title: str,
    description: str,
    *actions: rx.Component,
) -> rx.Component:
    """Canonical page heading with an optional action region."""
    return rx.flex(
        rx.box(
            rx.text(
                eyebrow.upper(),
                font_size="0.72rem",
                font_weight="800",
                letter_spacing="0.09em",
                color="var(--vitta-primary)",
            ),
            rx.heading(
                title,
                size="8",
                margin_top="0.35rem",
                letter_spacing="-0.035em",
                font_family="var(--vitta-font-display)",
            ),
            rx.text(
                description,
                color="var(--vitta-text-muted)",
                max_width="72ch",
                line_height="1.6",
                margin_top="0.45rem",
            ),
            min_width="0",
        ),
        (
            rx.hstack(
                *actions,
                spacing="2",
                align="center",
                flex_wrap="wrap",
                width=rx.breakpoints(initial="100%", md="auto"),
                min_width="0",
            )
            if actions
            else rx.fragment()
        ),
        direction=rx.breakpoints(initial="column", md="row"),
        justify="between",
        align=rx.breakpoints(initial="stretch", md="end"),
        gap="1rem",
        width="100%",
        class_name="vitta-page-header",
    )


def section_panel(*children, padding=None, **props) -> rx.Component:
    """Render a durable operational section using the canonical product surface."""
    return rx.box(
        *children,
        width="100%",
        padding=(
            padding
            if padding is not None
            else rx.breakpoints(initial="1rem", sm="1.25rem")
        ),
        background="var(--vitta-surface)",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-panel)",
        box_shadow="var(--vitta-shadow-xs)",
        **props,
    )


def metric_card(label: str, value, detail: str = "") -> rx.Component:
    """Compact factual metric card. Caller must supply real persisted values."""
    return rx.box(
        rx.hstack(
            rx.text(
                label,
                size="2",
                font_weight="700",
                color="var(--vitta-text-muted)",
            ),
            rx.box(class_name="vitta-metric-mark", aria_hidden="true"),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.text(
            value,
            font_size="1.75rem",
            font_weight="800",
            letter_spacing="-0.04em",
            font_family="var(--vitta-font-display)",
            class_name="vitta-tabular",
            margin_top="0.55rem",
        ),
        (
            rx.text(
                detail,
                size="1",
                color="var(--vitta-text-subtle)",
                margin_top="0.15rem",
            )
            if detail
            else rx.fragment()
        ),
        class_name="vitta-metric-card",
    )


def empty_state(
    icon: str,
    title: str,
    description: str,
    *actions: rx.Component,
    min_height: str = "14rem",
    padding: str = "1.5rem",
) -> rx.Component:
    """Honest empty state that never invents records or disabled pseudo-actions."""
    return rx.center(
        rx.vstack(
            rx.box(
                rx.icon(icon, size=22),
                class_name="vitta-empty-icon",
            ),
            rx.heading(title, size="4", text_align="center"),
            rx.text(
                description,
                color="var(--vitta-text-muted)",
                size="2",
                line_height="1.55",
                max_width="52ch",
                text_align="center",
            ),
            (
                rx.hstack(*actions, spacing="2", justify="center", flex_wrap="wrap")
                if actions
                else rx.fragment()
            ),
            spacing="3",
            align="center",
        ),
        min_height=min_height,
        padding=padding,
        width="100%",
        class_name="vitta-empty-state",
    )


def _product_shell(role: Role, active: str, *children: rx.Component) -> rx.Component:
    return rx.box(
        authenticated_sidebar(role, active),
        rx.box(
            authenticated_topbar(),
            rx.el.main(
                rx.vstack(
                    *children,
                    spacing="5",
                    align="stretch",
                    width="100%",
                ),
                class_name="vitta-page",
            ),
            class_name="vitta-main",
        ),
        class_name="vitta-shell",
    )


def dashboard_shell(role: Role, title: str, description: str) -> rx.Component:
    """Render an honest protected empty shell for a role without its business module."""
    active = {
        Role.ADMINISTRADOR: "administracao",
        Role.RECEPCIONISTA: "recepcao",
        Role.MEDICO: "atendimento",
        Role.FINANCEIRO: "financeiro",
        Role.PACIENTE: "consultas-paciente",
    }[role]
    return protected_workspace(
        role,
        page_header("Vitta-One", title, description),
        rx.cond(
            AuthState.shell_error != "",
            error_banner(AuthState.shell_error),
            rx.fragment(),
        ),
        section_panel(
            empty_state(
                "layers",
                "Módulo ainda não implementado",
                "A estrutura de acesso está pronta. Os dados e ações deste módulo serão adicionados por uma change específica do OpenSpec.",
            )
        ),
        active=active,
    )


def protected_workspace(
    role: Role,
    *children: rx.Component,
    active: str | None = None,
    verified_path: str | None = None,
) -> rx.Component:
    """Render an authorized operational workspace using the premium product shell."""
    active_key = active or {
        Role.ADMINISTRADOR: "administracao",
        Role.RECEPCIONISTA: "recepcao",
        Role.MEDICO: "atendimento",
        Role.FINANCEIRO: "financeiro",
        Role.PACIENTE: "consultas-paciente",
    }[role]

    protected_content = _product_shell(role, active_key, *children)

    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == role.value)
        & (AuthState.verified_path == (verified_path or role.dashboard_path)),
        protected_content,
        loading_surface(),
    )


def admin_preview_workspace(
    verified_path: str,
    active: str,
    *children: rx.Component,
) -> rx.Component:
    """Render one local-only Administrator QA projection after explicit server authorization."""
    return rx.cond(
        AuthState.auth_checked
        & AuthState.local_admin_preview
        & (AuthState.current_role == Role.ADMINISTRADOR.value)
        & (AuthState.verified_path == verified_path),
        _product_shell(Role.ADMINISTRADOR, active, *children),
        loading_surface(),
    )
