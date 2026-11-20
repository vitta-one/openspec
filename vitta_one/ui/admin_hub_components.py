"""Task-oriented administration navigation, without duplicating business actions."""

import reflex as rx

from vitta_one.ui.components import breadcrumb, error_banner, field_label, page_header, section_panel, empty_state, summary_metric
from vitta_one.auth.staff_state import AdminStaffState
from vitta_one.admin_dashboard.state import AdminDashboardState
from vitta_one.ui.staff_components import admin_staff_panel


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
    icon = "users_round" if title == "Equipe e acessos" else "calendar_days"
    return rx.el.section(
        rx.hstack(
            rx.icon(icon, size=22, color="var(--vitta-primary)"),
            rx.heading(title, size="4", class_name="vitta-admin-hub-heading"),
            align="center", gap="3", width="100%",
        ),
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
    """Task-oriented admin landing page with server-derived aggregate metrics."""
    return rx.vstack(
        page_header(
            "Administração",
            "Gestão da clínica",
            "Controle equipe, agenda, especialidades e configurações gerais.",
            show_art=True,
            art_source="/clinic-operational-hero.svg",
        ),
        rx.cond(
            AdminDashboardState.error_message != "",
            rx.vstack(
                error_banner(AdminDashboardState.error_message),
                rx.button(
                    "Tentar novamente",
                    type="button",
                    variant="outline",
                    color_scheme="teal",
                    on_click=AdminDashboardState.load,
                ),
                align="start",
                spacing="3",
                width="100%",
            ),
            rx.cond(
                AdminDashboardState.has_loaded,
                rx.grid(
                    _admin_metric(
                        "Profissionais",
                        AdminDashboardState.active_professionals,
                        "users",
                        "/admin/profissionais",
                    ),
                    _admin_metric(
                        "Especialidades",
                        AdminDashboardState.active_specialties,
                        "stethoscope",
                        "/admin/especialidades",
                    ),
                    _admin_metric(
                        "Consultas (hoje)",
                        AdminDashboardState.consultations_today,
                        "calendar_days",
                        "/admin/horarios",
                    ),
                    _admin_metric(
                        "Funcionários",
                        AdminDashboardState.staff_accounts,
                        "users_round",
                        "/admin/funcionarios",
                    ),
                    columns=rx.breakpoints(initial="1", sm="2", xl="4"),
                    gap="3",
                    width="100%",
                    class_name="vitta-admin-metrics",
                ),
                rx.center(
                    rx.spinner(size="3", color="var(--vitta-primary)"),
                    rx.text("Carregando indicadores da clínica…", size="2", color="var(--vitta-text-muted)"),
                    gap="3",
                    min_height="8rem",
                    width="100%",
                    role="status",
                    aria_live="polite",
                ),
            ),
        ),
        rx.grid(
            section_panel(_admin_group(
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
            )),
            section_panel(_admin_group(
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
            )),
            columns=rx.breakpoints(initial="1", lg="repeat(2, minmax(0, 1fr))"),
            gap="4", align="stretch", width="100%",
            class_name="vitta-admin-hub-groups",
        ),
        section_panel(
            rx.flex(
                rx.vstack(
                    rx.heading("Acessos rápidos", size="4"),
                    rx.text("Tarefas administrativas do dia a dia.", size="2", color="var(--vitta-text-muted)"),
                    align="start",
                    spacing="1",
                ),
                rx.flex(
                    _admin_quick_link("Ver agenda", "/admin/agenda", "calendar_days"),
                    _admin_quick_link("Profissionais", "/admin/profissionais", "users_round"),
                    _admin_quick_link("Novo funcionário", "/admin/funcionarios/novo", "user_plus"),
                    _admin_quick_link("Configurações", "/admin/configuracoes", "settings"),
                    gap="2",
                    flex_wrap="wrap",
                    justify="end",
                ),
                justify="between",
                align="center",
                gap="4",
                flex_wrap="wrap",
                width="100%",
                class_name="vitta-admin-quick-access",
            ),
            class_name="vitta-admin-quick-panel",
        ),
        spacing="4",
        align="stretch",
        width="100%",
        class_name="vitta-admin-hub",
    )


def _admin_metric(label: str, value, icon: str, href: str) -> rx.Component:
    return rx.link(
        rx.flex(
            rx.box(rx.icon(icon, size=22), class_name="vitta-admin-metric-icon"),
            rx.vstack(
                rx.text(label, size="2", color="var(--vitta-text-muted)", font_weight="650"),
                rx.text(value, size="6", color="var(--vitta-text)", font_weight="800", class_name="vitta-tabular"),
                align="start",
                spacing="0",
                min_width="0",
            ),
            rx.icon("chevron_right", size=19, color="var(--vitta-text-muted)"),
            gap="3",
            align="center",
            width="100%",
        ),
        href=href,
        class_name="vitta-admin-metric",
        aria_label=label,
    )


def _admin_quick_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(rx.icon(icon, size=17), rx.text(label, font_weight="700"), gap="2", align="center"),
        href=href,
        class_name="vitta-admin-quick-link",
    )


def _employee_details_link(employee) -> rx.Component:
    """Use the approved eye action while naming the destination accessibly."""
    return rx.link(
        rx.icon("eye", size=18, aria_hidden="true"),
        rx.text("Ver detalhes de ", employee["name"], class_name="vitta-sr-only"),
        href=employee["href"].to(str),
        class_name="vitta-context-link vitta-staff-details-link",
    )


def _employee_table_row(employee) -> rx.Component:
    return rx.table.row(
        rx.table.row_header_cell(
            rx.hstack(
                rx.box(
                    rx.icon("user_round", size=22, aria_hidden="true"),
                    class_name="vitta-staff-table-avatar",
                    aria_hidden="true",
                ),
                rx.text(employee["name"], font_weight="700", overflow_wrap="anywhere"),
                align="center", gap="3", min_width="0",
            )
        ),
        rx.table.cell(
            rx.text(employee["email"], size="2", overflow_wrap="anywhere")
        ),
        rx.table.cell(
            rx.badge(employee["role_label"], color_scheme="teal", variant="soft",
                     high_contrast=True)
        ),
        rx.table.cell(
            rx.badge(employee["access_status"], color_scheme="green", variant="soft",
                     high_contrast=True)
        ),
        rx.table.cell(_employee_details_link(employee)),
        class_name="vitta-staff-table-row",
    )


def _employee_mobile_row(employee) -> rx.Component:
    """A linear reading order keeps every field and action accessible on mobile."""
    return rx.flex(
        rx.vstack(
            rx.text(employee["name"], font_weight="700", overflow_wrap="anywhere"),
            rx.text(employee["email"], size="2", color="var(--vitta-text-muted)",
                    overflow_wrap="anywhere"),
            rx.badge(employee["role_label"], color_scheme="teal", variant="soft",
                     high_contrast=True),
            rx.badge(employee["access_status"], color_scheme="green", variant="soft",
                     high_contrast=True),
            spacing="1", align="start", min_width="0",
        ),
        _employee_details_link(employee),
        direction="column", align="start", gap="2",
        class_name="vitta-staff-mobile-row",
    )


def _staff_directory_results() -> rx.Component:
    return rx.cond(
        AdminStaffState.is_loading,
        rx.center(
            rx.vstack(
                rx.spinner(size="3", color="var(--vitta-primary)"),
                rx.text("Carregando funcionários…", color="var(--vitta-text-muted)", size="2"),
                align="center", spacing="3",
            ),
            role="status", aria_live="polite", min_height="12rem", width="100%",
        ),
        rx.cond(
            AdminStaffState.error != "",
            rx.vstack(
                error_banner(AdminStaffState.error),
                rx.button("Tentar novamente", type="button", variant="outline",
                          color_scheme="teal", on_click=AdminStaffState.load),
                align="start", spacing="3", width="100%",
            ),
            rx.cond(
                AdminStaffState.paged_employees.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Funcionário"),
                                rx.table.column_header_cell("E-mail"),
                                rx.table.column_header_cell("Perfil"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Ações"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(AdminStaffState.paged_employees, _employee_table_row),
                        ),
                        size="2", variant="ghost", width="100%",
                        class_name="vitta-staff-table",
                    ),
                    rx.vstack(
                        rx.foreach(AdminStaffState.paged_employees, _employee_mobile_row),
                        spacing="0", align="stretch", width="100%",
                        class_name="vitta-staff-mobile",
                    ),
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("users", size=25, color="var(--vitta-primary)"),
                        rx.heading(
                            rx.cond(AdminStaffState.has_employee_filters,
                                    "Nenhum resultado para os filtros",
                                    "Nenhum funcionário cadastrado"),
                            size="3",
                        ),
                        rx.text(
                            rx.cond(AdminStaffState.has_employee_filters,
                                    "Altere a busca ou limpe os filtros para ver a equipe.",
                                    "Cadastre um funcionário para começar a gerenciar os acessos."),
                            color="var(--vitta-text-muted)", size="2",
                            text_align="center",
                        ),
                        rx.cond(
                            AdminStaffState.has_employee_filters,
                            rx.button("Limpar filtros", type="button", variant="outline",
                                      color_scheme="teal",
                                      on_click=AdminStaffState.clear_employee_filters),
                            rx.link("Novo funcionário", href="/admin/funcionarios/novo",
                                    class_name="vitta-primary-action"),
                        ),
                        align="center", spacing="3",
                    ),
                    padding="2rem 1rem", min_height="12rem", width="100%",
                ),
            ),
        ),
    )


def admin_staff_type_workspace() -> rx.Component:
    """A task-first, read-only employee directory with real search and filtering."""
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
        rx.cond(
            AdminStaffState.error == "",
            rx.cond(
                AdminStaffState.is_loading,
                rx.center(
                    rx.spinner(size="2"),
                    rx.text("Carregando indicadores da equipe…", size="2",
                            color="var(--vitta-text-muted)"),
                    gap="3", min_height="5rem", width="100%", role="status",
                ),
                rx.grid(
                    summary_metric("Total de funcionários", AdminStaffState.employee_count, "users_round"),
                    summary_metric("Recepcionistas", AdminStaffState.reception_account_count, "user_round"),
                    summary_metric("Médicos", AdminStaffState.medical_account_count, "stethoscope"),
                    summary_metric("Administradores", AdminStaffState.administrator_account_count, "settings"),
                    summary_metric("Outros perfis", AdminStaffState.other_account_count, "layers"),
                    columns=rx.breakpoints(initial="1", sm="2", md="3", xl="5"),
                    gap="3", width="100%", class_name="vitta-directory-summary",
                ),
            ),
            rx.fragment(),
        ),
        section_panel(
            rx.vstack(
                rx.box(
                    rx.heading("Equipe cadastrada", size="4"),
                    rx.text(
                        "Contas médicas e de recepção, com acesso por perfil.",
                        color="var(--vitta-text-muted)", size="2", margin_top="0.35rem",
                    ),
                    width="100%",
                ),
                rx.grid(
                    rx.box(
                        rx.el.label(
                            "Buscar funcionário por nome, e-mail ou perfil",
                            html_for="staff-directory-search",
                            class_name="vitta-sr-only",
                        ),
                        rx.flex(
                            rx.box(
                                rx.icon("search", size=18, aria_hidden="true"),
                                rx.el.input(
                                    id="staff-directory-search", type="search",
                                    placeholder="Buscar por nome, e-mail ou perfil...",
                                    aria_label="Buscar funcionário por nome, e-mail ou perfil",
                                    class_name="vitta-input vitta-staff-search-input",
                                    value=AdminStaffState.employee_search,
                                    on_change=AdminStaffState.update_employee_search,
                                    width="100%", min_width="0",
                                ),
                                class_name="vitta-staff-search-control",
                            ),
                            rx.cond(
                                AdminStaffState.employee_search != "",
                                rx.button("Limpar busca", type="button", variant="ghost",
                                          color_scheme="teal", size="2",
                                          on_click=AdminStaffState.update_employee_search("")),
                                rx.fragment(),
                            ),
                            gap="2", align="center", width="100%",
                        ),
                        min_width="0",
                    ),
                    rx.box(
                        field_label("Filtrar por perfil", "staff-directory-role"),
                        rx.select.root(
                            rx.select.trigger(
                                id="staff-directory-role", width="100%",
                                class_name="vitta-select-trigger",
                                aria_label="Filtrar funcionários por perfil",
                            ),
                            rx.select.content(
                                rx.select.item("Todos os perfis", value="todos"),
                                rx.select.item("Médico", value="MEDICO"),
                                rx.select.item("Recepcionista", value="RECEPCIONISTA"),
                                position="popper",
                            ),
                            value=AdminStaffState.employee_role,
                            on_change=AdminStaffState.update_employee_role,
                            size="3",
                        ),
                        width=rx.breakpoints(initial="100%", sm="14rem"),
                    ),
                    rx.cond(
                        AdminStaffState.has_employee_filters,
                        rx.button("Limpar filtros", type="button", variant="outline",
                                  color_scheme="teal", size="2",
                                  on_click=AdminStaffState.clear_employee_filters),
                        rx.fragment(),
                    ),
                    columns=rx.breakpoints(
                        initial="1",
                        xl="minmax(0, 1fr) minmax(14rem, 17rem) auto",
                    ),
                    gap="3", align="end", width="100%",
                    class_name="vitta-staff-toolbar",
                ),
                _staff_directory_results(),
                rx.cond(
                    (AdminStaffState.error == "") & (~AdminStaffState.is_loading),
                    rx.flex(
                        rx.text(
                            "Mostrando ", AdminStaffState.page_range_start, "–",
                            AdminStaffState.page_range_end, " de ",
                            AdminStaffState.filtered_employees.length(), " funcionários",
                            size="2", color="var(--vitta-text-muted)",
                        ),
                        rx.hstack(
                            rx.text("Itens por página", size="2"),
                            rx.select.root(
                                rx.select.trigger(
                                    width="4.5rem",
                                    class_name="vitta-select-trigger vitta-staff-page-size",
                                    aria_label="Itens por página",
                                ),
                                rx.select.content(
                                    rx.select.item("10", value="10"),
                                    rx.select.item("25", value="25"),
                                    rx.select.item("50", value="50"),
                                    position="popper",
                                ),
                                value=AdminStaffState.page_size_value,
                                on_change=AdminStaffState.update_employee_page_size,
                                size="2",
                            ),
                            rx.hstack(
                                rx.button(
                                    rx.icon("chevron_left", size=17),
                                    type="button", variant="outline", color_scheme="gray",
                                    class_name="vitta-staff-page-control",
                                    on_click=AdminStaffState.move_employee_page(-1),
                                    disabled=AdminStaffState.current_page <= 1,
                                    aria_label="Página anterior",
                                ),
                                rx.el.span(
                                    AdminStaffState.current_page,
                                    class_name="vitta-staff-page-control is-current",
                                    aria_current="page",
                                ),
                                rx.button(
                                    rx.icon("chevron_right", size=17),
                                    type="button", variant="outline", color_scheme="gray",
                                    class_name="vitta-staff-page-control",
                                    on_click=AdminStaffState.move_employee_page(1),
                                    disabled=AdminStaffState.current_page >= AdminStaffState.total_pages,
                                    aria_label="Próxima página",
                                ),
                                gap="2", align="center",
                                class_name="vitta-staff-pagination-controls",
                            ),
                            gap="2", align="center",
                            class_name="vitta-staff-footer-controls",
                        ),
                        justify="between", gap="3", align="center",
                        flex_wrap="wrap", width="100%",
                        class_name="vitta-staff-footer",
                    ),
                    rx.fragment(),
                ),
                spacing="4", align="stretch", width="100%",
            )
        ),
        spacing="4", align="stretch", width="100%",
    )


def admin_staff_create_workspace() -> rx.Component:
    """Página única: identidade compartilhada e campos condicionais por role."""
    return rx.vstack(
        breadcrumb(("Administração", "/admin"), ("Funcionários", "/admin/funcionarios"),
                   ("Novo funcionário", None)),
        rx.vstack(
            page_header(
                "Equipe",
                "Novo funcionário",
                "Identifique o colaborador e defina o acesso de acordo com o perfil.",
                title_margin_top="0.7rem",
            ),
            admin_staff_panel(),
            spacing="1", align="stretch", width="100%",
        ),
        spacing="5", align="stretch", width="100%",
        class_name="vitta-staff-create-workspace",
    )


def _employee_detail_field(label: str, value) -> rx.Component:
    """One readable, compact label/value pair with safe wrapping on narrow screens."""
    return rx.vstack(
        rx.text(label, size="2", color="var(--vitta-text-muted)"),
        rx.text(
            value,
            size="3",
            font_weight="650",
            color="var(--vitta-text)",
            overflow_wrap="anywhere",
            width="100%",
        ),
        spacing="1",
        align="start",
        min_width="0",
        width="100%",
    )


def _employee_detail_content() -> rx.Component:
    """Permanent employee record; never imply a new registration on revisit."""
    return rx.vstack(
        section_panel(
            rx.vstack(
                rx.heading("Informações do funcionário", size="4"),
                rx.flex(
                    rx.box(
                        rx.icon("user_round", size=25, color="var(--vitta-primary)"),
                        class_name="vitta-admin-action-icon",
                        flex_shrink="0",
                        aria_hidden="true",
                    ),
                    rx.vstack(
                        rx.cond(
                            AdminStaffState.employee_detail["has_name"],
                            rx.heading(
                                AdminStaffState.employee_detail["name"],
                                size="6",
                                overflow_wrap="anywhere",
                            ),
                            rx.text(
                                "Nome não informado",
                                font_weight="650",
                                color="var(--vitta-text-muted)",
                                size="4",
                            ),
                        ),
                        rx.badge(
                            AdminStaffState.employee_detail["role_label"],
                            color_scheme="teal",
                            variant="soft",
                            high_contrast=True,
                            width="fit-content",
                        ),
                        spacing="2",
                        align="start",
                        min_width="0",
                        width="100%",
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    align="start",
                    gap="3",
                    width="100%",
                ),
                rx.separator(),
                rx.heading("Dados de acesso", size="3"),
                _employee_detail_field(
                    "E-mail de acesso",
                    AdminStaffState.employee_detail["email"],
                ),
                spacing="4",
                align="stretch",
                width="100%",
            )
        ),
        rx.cond(
            AdminStaffState.employee_detail["professional_identifier"] != "",
            section_panel(
                rx.vstack(
                    rx.heading("Vínculo profissional", size="4"),
                    rx.flex(
                        _employee_detail_field(
                            "Identificador do profissional",
                            AdminStaffState.employee_detail["professional_identifier"],
                        ),
                        _employee_detail_field(
                            "Situação do vínculo",
                            AdminStaffState.employee_detail["professional_status"],
                        ),
                        direction=rx.breakpoints(initial="column", md="row"),
                        align="start",
                        gap="4",
                        width="100%",
                    ),
                    rx.cond(
                        AdminStaffState.employee_detail["specialties"] != "",
                        _employee_detail_field(
                            "Especialidades vinculadas",
                            AdminStaffState.employee_detail["specialties"],
                        ),
                        rx.fragment(),
                    ),
                    rx.link(
                        "Gerenciar médicos",
                        href="/admin/profissionais",
                        class_name="vitta-context-link",
                        aria_label="Abrir diretório de profissionais para gerenciar médicos",
                    ),
                    align="stretch",
                    spacing="4",
                    width="100%",
                )
            ),
            rx.fragment(),
        ),
        rx.text(
            "Identificador interno do cadastro: #",
            AdminStaffState.employee_detail["id"],
            size="1",
            color="var(--vitta-text-muted)",
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )


def admin_staff_detail_workspace() -> rx.Component:
    """Read-only authorized staff profile with explicit retrieval states."""
    return rx.vstack(
        breadcrumb(
            ("Administração", "/admin"),
            ("Funcionários", "/admin/funcionarios"),
            ("Ficha do funcionário", None),
        ),
        rx.vstack(
            page_header(
                "Equipe",
                "Ficha do funcionário",
                "Consulte os dados de identificação, acesso e vínculo profissional.",
                rx.link(
                    rx.hstack(
                        rx.icon("arrow_left", size=16),
                        rx.text("Voltar aos funcionários"),
                        spacing="2",
                        align="center",
                    ),
                    href="/admin/funcionarios",
                    class_name="vitta-context-link",
                ),
            ),
            rx.cond(
                AdminStaffState.detail_matches_route,
                _employee_detail_content(),
                rx.cond(
                    AdminStaffState.detail_status == "not_found",
                    section_panel(
                        empty_state(
                            "user_round_x",
                            "Funcionário não encontrado",
                            "O cadastro solicitado não existe ou não está disponível nesta lista.",
                            rx.link(
                                "Voltar aos funcionários",
                                href="/admin/funcionarios",
                                class_name="vitta-context-link",
                            ),
                        )
                    ),
                    rx.cond(
                        AdminStaffState.detail_status == "error",
                        section_panel(
                            rx.vstack(
                                error_banner(
                                    "Não foi possível consultar os dados do funcionário. Tente novamente."
                                ),
                                rx.button(
                                    "Tentar novamente",
                                    type="button",
                                    variant="outline",
                                    color_scheme="teal",
                                    on_click=AdminStaffState.load_detail,
                                ),
                                align="start",
                                spacing="3",
                                width="100%",
                            )
                        ),
                        rx.center(
                            rx.hstack(
                                rx.spinner(size="2"),
                                rx.text("Carregando ficha do funcionário…", size="2"),
                                align="center",
                                spacing="3",
                            ),
                            min_height="12rem",
                            width="100%",
                            role="status",
                            aria_live="polite",
                        ),
                    ),
                ),
            ),
            spacing="4",
            align="stretch",
            width="100%",
            max_width="58rem",
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )
