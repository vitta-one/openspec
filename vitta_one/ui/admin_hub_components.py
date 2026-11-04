"""Task-oriented administration navigation, without duplicating business actions."""

import reflex as rx

from vitta_one.ui.components import breadcrumb, page_header, section_panel
from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.staff_components import admin_staff_panel
from vitta_one.ui.admin_directory_components import medical_registration_form_panel


def _admin_destination(title: str, description: str, href: str, icon: str) -> rx.Component:
    """A semantic navigation link with an explicit destination and a large target."""
    return rx.link(
        rx.flex(
            rx.box(rx.icon(icon, size=20), class_name="vitta-admin-action-icon"),
            rx.vstack(
                rx.text(title, font_weight="750", color="var(--vitta-text)", size="3"),
                rx.text(description, size="2", color="var(--vitta-text-muted)", line_height="1.5"),
                spacing="1", align="start", flex="1", min_width="0",
            ),
            rx.icon("chevron_right", size=19, color="var(--vitta-text-muted)", flex_shrink="0"),
            align="center", gap="3", width="100%",
        ),
        href=href,
        class_name="vitta-admin-action",
        aria_label=f"{title}. {description}",
    )


def _admin_group(title: str, *destinations: rx.Component) -> rx.Component:
    """Group related destinations into one compact, keyboard-friendly list."""
    return rx.el.section(
        rx.heading(title, size="4", class_name="vitta-admin-hub-heading"),
        rx.vstack(
            *destinations,
            spacing="0",
            align="stretch",
            width="100%",
            class_name="vitta-admin-hub-list",
        ),
        class_name="vitta-admin-hub-group",
    )


def admin_hub_workspace() -> rx.Component:
    """Compact landing page with real task links and no fictitious metrics."""
    return rx.vstack(
        page_header(
            "Administração",
            "Gestão da clínica",
            "Acesse as tarefas administrativas da clínica.",
        ),
        rx.box(
            _admin_group(
                "Equipe e acessos",
                _admin_destination(
                    "Criar funcionário",
                    "Cadastre um médico ou recepcionista.",
                    "/admin/funcionarios/novo", "user_plus",
                ),
                _admin_destination(
                    "Profissionais",
                    "Consulte e gerencie os médicos cadastrados.",
                    "/admin/profissionais", "stethoscope",
                ),
                _admin_destination(
                    "Especialidades",
                    "Organize as áreas de atendimento da clínica.",
                    "/admin/especialidades", "list_filter",
                ),
            ),
            _admin_group(
                "Agenda e clínica",
                _admin_destination(
                    "Gerenciar horários",
                    "Configure expedientes e consulte a disponibilidade médica.",
                    "/admin/horarios", "calendar_clock",
                ),
                _admin_destination(
                    "Configurações da clínica",
                    "Consulte as informações exibidas no portal do paciente.",
                    "/admin/configuracoes", "settings",
                ),
            ),
            class_name="vitta-admin-hub-groups",
        ),
        spacing="4",
        align="stretch",
        width="100%",
        class_name="vitta-admin-hub",
    )


def _employee_row(employee) -> rx.Component:
    return rx.link(
        rx.flex(
            rx.hstack(
                rx.box(rx.icon("user_round", size=19), class_name="vitta-admin-action-icon"),
                rx.vstack(
                    rx.text(employee["name"], font_weight="700", overflow_wrap="anywhere"),
                    rx.text(employee["email"], color="var(--vitta-text-muted)", size="2"),
                    rx.text(employee["role_label"], color="var(--vitta-primary)", size="1"),
                    spacing="1", align="start",
                ),
                gap="3", align="center",
            ),
            rx.icon("chevron_right", size=18, color="var(--vitta-text-muted)"),
            justify="between", align="center", gap="3", width="100%",
        ),
        href=employee["href"].to(str),
        class_name="vitta-staff-row",
    )


def admin_staff_type_workspace() -> rx.Component:
    """Paginated employee directory, separated from onboarding forms."""
    return rx.vstack(
        breadcrumb(("Administração", "/admin"), ("Funcionários", None)),
        page_header(
            "Equipe",
            "Funcionários",
            "Consulte os acessos cadastrados ou adicione um novo membro da clínica.",
            rx.link(
                rx.hstack(
                    rx.icon("user_plus", size=17, flex_shrink="0"),
                    rx.text("Novo funcionário", font_weight="700"),
                    spacing="2", align="center", justify="center",
                ),
                href="/admin/funcionarios/novo",
                class_name="vitta-primary-action vitta-staff-create-action",
                aria_label="Cadastrar novo funcionário",
            ),
        ),
        section_panel(
            rx.vstack(
                rx.flex(
                    rx.box(
                        rx.heading("Equipe cadastrada", size="4"),
                        rx.text("Contas médicas e de recepção, com acesso por perfil.",
                                color="var(--vitta-text-muted)", size="2", margin_top="0.35rem"),
                    ),
                    rx.box(
                        rx.el.input(
                            type="search", placeholder="Buscar por e-mail ou perfil",
                            aria_label="Pesquisar funcionários", class_name="vitta-input",
                            value=AdminStaffState.employee_search,
                            on_change=AdminStaffState.update_employee_search,
                        ),
                        width=rx.breakpoints(initial="100%", md="min(20rem, 100%)"),
                    ),
                    gap="4", align="center", justify="between", flex_wrap="wrap", width="100%",
                ),
                rx.cond(
                    AdminStaffState.paged_employees.length() > 0,
                    rx.vstack(
                        rx.foreach(AdminStaffState.paged_employees, _employee_row),
                        spacing="2", align="stretch", width="100%",
                        class_name="vitta-staff-directory",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("users", size=24, color="var(--vitta-primary)"),
                            rx.heading("Nenhum funcionário encontrado", size="3"),
                            rx.text("Adicione um funcionário ou ajuste os termos da pesquisa.",
                                    color="var(--vitta-text-muted)", size="2"),
                            align="center", spacing="2",
                        ),
                        padding="2rem", min_height="12rem", width="100%",
                    ),
                ),
                rx.flex(
                    rx.text(AdminStaffState.employees.length(), " funcionários cadastrados",
                            color="var(--vitta-text-muted)", size="2"),
                    rx.hstack(
                        rx.button("Anterior", type="button", variant="outline", color_scheme="teal",
                                  on_click=AdminStaffState.move_employee_page(-1),
                                  disabled=AdminStaffState.current_page <= 1),
                        rx.text(AdminStaffState.page_label, size="2", font_weight="650"),
                        rx.button("Próxima", type="button", variant="outline", color_scheme="teal",
                                  on_click=AdminStaffState.move_employee_page(1),
                                  disabled=AdminStaffState.current_page >= AdminStaffState.total_pages),
                        gap="3", align="center",
                    ),
                    justify="between", gap="3", align="center", flex_wrap="wrap", width="100%",
                ),
                spacing="5", align="stretch", width="100%",
            )
        ),
        spacing="5", align="stretch", width="100%",
    )


def admin_staff_create_workspace() -> rx.Component:
    """One employee entry point; selecting a role reveals only its valid form."""
    return rx.vstack(
        breadcrumb(("Administração", "/admin"), ("Funcionários", "/admin/funcionarios"),
                   ("Novo funcionário", None)),
        page_header(
            "Equipe",
            "Novo funcionário",
            "Escolha o perfil de acesso. Os campos serão adaptados automaticamente.",
        ),
        section_panel(
            rx.vstack(
                rx.box(
                    rx.heading("Perfil do funcionário", size="4"),
                    rx.text("Essa escolha define as permissões e os dados obrigatórios da conta.",
                            size="2", color="var(--vitta-text-muted)", margin_top="0.35rem"),
                    width="100%",
                ),
                rx.box(
                    rx.select.root(
                        rx.select.trigger(id="staff-create-role", width="100%",
                                          placeholder="Selecione um perfil",
                                          class_name="vitta-select-trigger",
                                          aria_label="Perfil do funcionário"),
                        rx.select.content(
                            rx.select.item("Médico", value="medico"),
                            rx.select.item("Recepcionista", value="recepcionista"),
                            position="popper",
                        ),
                        value=AdminStaffState.creation_profile,
                        on_change=AdminStaffState.select_creation_profile,
                        size="3",
                    ),
                    width="100%", max_width="32rem",
                ),
                spacing="4", width="100%", align="stretch",
            )
        ),
        rx.cond(
            AdminStaffState.creation_profile == "medico",
            rx.cond(
                AdminDirectoryState.is_loading,
                rx.center(rx.spinner(size="3"), min_height="10rem", width="100%"),
                medical_registration_form_panel(),
            ),
            rx.cond(AdminStaffState.creation_profile == "recepcionista",
                    admin_staff_panel(),
                    rx.fragment()),
        ),
        spacing="4", align="stretch", width="100%",
    )


def admin_staff_detail_workspace() -> rx.Component:
    """Read-only proof of creation; no editable or sensitive credentials shown."""
    return rx.vstack(
        breadcrumb(("Administração", "/admin"), ("Funcionários", "/admin/funcionarios"),
                   ("Ficha do funcionário", None)),
        page_header("Equipe", "Ficha do funcionário",
                    "Cadastro concluído. Consulte o perfil e a identificação do acesso."),
        section_panel(
            rx.vstack(
                rx.hstack(
                    rx.icon("badge_check", size=24, color="var(--vitta-primary)"),
                    rx.heading("Funcionário cadastrado", size="4"),
                    gap="3", align="center",
                ),
                rx.separator(),
                rx.text("Nome", color="var(--vitta-text-muted)", size="2"),
                rx.text(AdminStaffState.employee_detail["name"], font_weight="700", size="4"),
                rx.text("E-mail de acesso", color="var(--vitta-text-muted)", size="2"),
                rx.text(AdminStaffState.employee_detail["email"], font_weight="700", size="4"),
                rx.text("Perfil", color="var(--vitta-text-muted)", size="2"),
                rx.badge(AdminStaffState.employee_detail["role_label"],
                         color_scheme="teal", variant="soft", high_contrast=True),
                rx.text("ID do cadastro: ", AdminStaffState.employee_detail["id"],
                        size="2", color="var(--vitta-text-muted)"),
                rx.link("Voltar aos funcionários", href="/admin/funcionarios",
                        class_name="vitta-context-link"),
                spacing="3", align="stretch", width="100%",
            )
        ),
        spacing="4", align="stretch", width="100%",
    )
