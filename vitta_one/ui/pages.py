"""Vitta-One public and protected page components."""

import reflex as rx

from vitta_one.auth.roles import Role
from vitta_one.auth.state import AuthState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.ui.admin_directory_components import admin_directory_workspace
from vitta_one.ui.components import (
    brand_logo,
    dashboard_shell,
    feedback_region,
    loading_surface,
    login_form,
    page_heading,
    protected_workspace,
    section_panel,
)
from vitta_one.ui.queue_components import (
    active_queue_panel,
    doctor_active_panel,
    doctor_waiting_summary,
    enqueue_panel,
    patient_identity_panel,
    reassess_panel,
    withdraw_panel,
)


def root_page() -> rx.Component:
    """Render only a neutral routing surface while the session is resolved."""
    return loading_surface("Abrindo o Vitta-One…")


def login_page() -> rx.Component:
    """Render a focused, image-led authentication entry point."""
    content = rx.box(
        rx.box(
            rx.box(
                brand_logo(),
                rx.box(
                    rx.text("ACESSO CLÍNICO", class_name="vitta-eyebrow"),
                    rx.heading("Bem-vindo ao Vitta-One", class_name="vitta-login-title"),
                    rx.text(
                        "Entre para acessar seu espaço de trabalho da clínica com segurança.",
                        class_name="vitta-login-copy",
                    ),
                    margin_top="2.4rem",
                ),
                login_form(),
                rx.text(
                    "Vitta-One · Ambiente interno da clínica",
                    class_name="vitta-login-footnote",
                ),
                class_name="vitta-login-form-panel",
            ),
            rx.box(
                rx.image(
                    src="/medical-doctor.jpg",
                    alt="Profissional médica em ambiente clínico",
                    class_name="vitta-login-photo",
                ),
                rx.box(
                    rx.text("OPERAÇÃO CONECTADA", class_name="vitta-login-visual-kicker"),
                    rx.heading(
                        "Informação certa, no momento certo.",
                        class_name="vitta-login-visual-title",
                    ),
                    rx.text(
                        "Recepção, equipe clínica e administração trabalham sobre o mesmo contexto — com acesso separado por função.",
                        class_name="vitta-login-visual-copy",
                    ),
                    rx.flex(
                        rx.box("Recepção", class_name="vitta-visual-chip"),
                        rx.box("Atendimento", class_name="vitta-visual-chip"),
                        rx.box("Administração", class_name="vitta-visual-chip"),
                        gap="0.5rem",
                        wrap="wrap",
                        margin_top="1.2rem",
                    ),
                    class_name="vitta-login-visual-caption",
                ),
                class_name="vitta-login-visual",
            ),
            class_name="vitta-login-shell",
        ),
        class_name="vitta-login-canvas",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role == ""),
        content,
        loading_surface(),
    )


def _module_card(
    title: str,
    description: str,
    icon: str,
    href: str,
    status: str,
    status_tone: str = "available",
) -> rx.Component:
    return rx.link(
        section_panel(
            rx.flex(
                rx.box(rx.icon(icon, size=21), class_name="vitta-module-icon"),
                rx.badge(
                    status,
                    variant="soft",
                    color_scheme="teal" if status_tone == "available" else "gray",
                ),
                justify="between",
                align="center",
                width="100%",
            ),
            rx.heading(title, size="5", margin_top="1rem"),
            rx.text(
                description,
                color="var(--vitta-text-muted)",
                size="2",
                line_height="1.6",
                margin_top="0.45rem",
                min_height="3.2rem",
            ),
            rx.flex(
                rx.text("Abrir módulo", size="2", font_weight="650"),
                rx.icon("arrow_right", size=17),
                gap="0.45rem",
                align="center",
                color="var(--vitta-primary)",
                margin_top="1.15rem",
            ),
            class_name="vitta-module-card",
        ),
        href=href,
        underline="none",
        color="inherit",
    )


def admin_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_heading(
            "CENTRAL ADMINISTRATIVA",
            "Visão geral da clínica",
            "Acompanhe os módulos disponíveis no ambiente atual e navegue por toda a estrutura do Vitta-One sem misturar permissões operacionais.",
        ),
        rx.grid(
            _module_card(
                "Recepção",
                "Fluxo de pacientes, classificação informada e fila operacional.",
                "clipboard_list",
                "/admin/recepcao",
                "Operacional",
            ),
            _module_card(
                "Agenda",
                "Disponibilidade, agendamentos e consultas serão aplicados na próxima change.",
                "calendar",
                "/admin/agenda",
                "Planejado",
                "planned",
            ),
            _module_card(
                "Atendimento clínico",
                "A fila médica já existe; prontuário e registro clínico permanecem em evolução.",
                "stethoscope",
                "/admin/atendimento",
                "Parcial",
                "planned",
            ),
            _module_card(
                "Pacientes",
                "O cadastro mínimo de paciente já sustenta o fluxo da recepção.",
                "users",
                "/admin/pacientes",
                "Operacional",
            ),
            _module_card(
                "Financeiro",
                "Área protegida pronta para receber pagamentos e integração Asaas.",
                "wallet",
                "/admin/financeiro",
                "Estrutura pronta",
                "planned",
            ),
            _module_card(
                "Administração",
                "Gerencie especialidades, profissionais e vínculos com contas médicas.",
                "settings",
                "/admin/administracao",
                "Operacional",
            ),
            columns=rx.breakpoints(initial="1", md="2", xl="3"),
            gap="1rem",
            width="100%",
        ),
        section_panel(
            rx.flex(
                rx.box(
                    rx.text("PRÓXIMA EVOLUÇÃO", class_name="vitta-eyebrow"),
                    rx.heading("Agenda e consultas", size="5", margin_top="0.25rem"),
                    rx.text(
                        "O planejamento OpenSpec já está consolidado para disponibilidade por slots, agendamento, reagendamento e cancelamento. A interface não simula dados antes da implementação.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        line_height="1.6",
                        margin_top="0.35rem",
                        max_width="70ch",
                    ),
                ),
                rx.box(
                    rx.icon("shield_check", size=22),
                    class_name="vitta-module-icon",
                ),
                justify="between",
                align="center",
                gap="1rem",
                width="100%",
            ),
        ),
      active_nav="overview",
        page_title="Visão geral",
        required_path="/admin",
    )


def admin_reception_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_heading(
            "RECEPÇÃO · VISÃO ADMINISTRATIVA",
            "Fluxo operacional da recepção",
            "O Administrador enxerga a estrutura do fluxo, enquanto as mutações da fila continuam restritas à role Recepcionista no servidor.",
        ),
        rx.grid(
            section_panel(
                rx.box(rx.icon("user_plus", size=21), class_name="vitta-module-icon"),
                rx.heading("1. Identificar paciente", size="4", margin_top="0.9rem"),
                rx.text("Localizar pelo CPF ou cadastrar a identidade mínima.", size="2", color="var(--vitta-text-muted)", margin_top="0.35rem"),
            ),
            section_panel(
                rx.box(rx.icon("list_plus", size=21), class_name="vitta-module-icon"),
                rx.heading("2. Entrada na fila", size="4", margin_top="0.9rem"),
                rx.text("Registrar relato e prioridade recebida pela operação.", size="2", color="var(--vitta-text-muted)", margin_top="0.35rem"),
            ),
            section_panel(
                rx.box(rx.icon("refresh_cw", size=21), class_name="vitta-module-icon"),
                rx.heading("3. Reavaliar ou retirar", size="4", margin_top="0.9rem"),
                rx.text("Atualizar a classificação manual ou preservar a retirada com motivo.", size="2", color="var(--vitta-text-muted)", margin_top="0.35rem"),
            ),
            columns=rx.breakpoints(initial="1", md="3"),
            gap="1rem",
            width="100%",
        ),
        section_panel(
            rx.flex(
                rx.icon("lock_keyhole", size=20, color="var(--vitta-primary)"),
                rx.box(
                    rx.text("Separação de responsabilidades", font_weight="700"),
                    rx.text(
                        "Este painel é de supervisão estrutural. Para preservar o RBAC já aprovado, o Admin não executa ações da Recepção por esta rota.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        margin_top="0.2rem",
                    ),
                ),
                gap="0.8rem",
                align="start",
             )
        ),
        active_nav="reception",
        page_title="Recepção",
        required_path="/admin/recepcao",
    )


def admin_agenda_page() -> rx.Component:
    return dashboard_shell(
        Role.ADMINISTRADOR,
        "Agenda",
        "A navegação já está preparada para o fluxo visual dos mockups. O próximo backend de disponibilidade e agendamento está especificado em add-appointment-scheduling e ainda não deve exibir horários fictícios.",
        active_nav="agenda",
        required_path="/admin/agenda",
    )


def admin_clinical_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_heading(
            "ATENDIMENTO · VISÃO ADMINISTRATIVA",
            "Jornada clínica",
            "A fila médica está operacional. Registro de anamnese, diagnóstico, prescrições, exames e prontuário ainda dependem de changes clínicas próprias.",
        ),
        rx.flex(
            section_panel(
                rx.text("01", class_name="vitta-step-number"),
                rx.heading("Fila médica", size="4", margin_top="0.65rem"),
                rx.text("Chamada atômica do próximo paciente elegível.", size="2", color="var(--vitta-text-muted)", margin_top="0.3rem"),
            ),
            section_panel(
                rx.text("02", class_name="vitta-step-number"),
                rx.heading("Atendimento ativo", size="4", margin_top="0.65rem"),
                rx.text("Um atendimento ativo por identidade médica.", size="2", color="var(--vitta-text-muted)", margin_top="0.3rem"),
           ),
            section_panel(
                rx.text("03", class_name="vitta-step-number"),
                rx.heading("Registro clínico", size="4", margin_top="0.65rem"),
                rx.text("Próxima camada: prontuário, prescrição e exames.", size="2", color="var(--vitta-text-muted)", margin_top="0.3rem"),
           ),
            direction=rx.breakpoints(initial="column", lg="row"),
            gap="1rem",
            align="stretch",
            width="100%",
        ),
        active_nav="clinical",
        page_title="Atendimento clínico",
        required_path="/admin/atendimento",
    )


def admin_patients_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_heading(
            "PACIENTES · VISÃO ADMINISTRATIVA",
            "Base de pacientes",
            "Hoje o Vitta-One mantém a identidade mínima necessária para a fila: nome e CPF validado. O prontuário completo será construído sobre essa mesma identidade, sem duplicação.",
        ),
        section_panel(
            rx.flex(
                rx.box(rx.icon("users", size=22), class_name="vitta-module-icon"),
                rx.box(
                    rx.heading("Cadastro centralizado", size="5"),
                    rx.text(
                        "O cadastro operacional permanece no painel da Recepção. Esta rota administrativa evita inventar campos clínicos antes da especificação correspondente.",
                        color="var(--vitta-text-muted)",
                        size="2",
                        line_height="1.6",
                        margin_top="0.35rem",
                    ),
                ),
                gap="1rem",
                align="start",
            )
        ),
        active_nav="patients",
        page_title="Pacientes",
        required_path="/admin/pacientes",
    )


def admin_finance_page() -> rx.Component:
    return dashboard_shell(
        Role.ADMINISTRADOR,
        "Financeiro",
        "A área financeira já possui rota protegida própria, mas pagamentos e integração Asaas sandbox ainda não foram implementados. Nenhum valor é simulado neste painel.",
        active_nav="finance",
        required_path="/admin/financeiro",
    )


def admin_administration_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_directory_workspace(),
        active_nav="administration",
        page_title="Administração",
        required_path="/admin/administracao",
    )


def reception_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_heading(
            "OPERAÇÃO DA RECEPÇÃO",
            "Pacientes e fila de atendimento",
            "Cadastre ou localize o paciente, registre a prioridade recebida e acompanhe a fila ativa.",
        ),
        feedback_region(
            ReceptionQueueState.error_message,
            ReceptionQueueState.success_message,
        ),
        rx.flex(
            patient_identity_panel(),
            enqueue_panel(),
            direction=rx.breakpoints(initial="column", xl="row"),
            gap="1rem",
            align="start",
            width="100%",
        ),
        active_queue_panel(),
        reassess_panel(),
        withdraw_panel(),
        active_nav="reception",
        page_title="Recepção",
        required_path="/recepcao",
    )


def doctor_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_heading(
            "ATENDIMENTO CLÍNICO",
            "Fila médica",
            "Chame o próximo paciente elegível e finalize somente o atendimento associado à sua sessão.",
        ),
        feedback_region(
            DoctorQueueState.error_message,
            DoctorQueueState.success_message,
        ),
        doctor_waiting_summary(),
        rx.cond(
            DoctorQueueState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text(
                        "Carregando atendimento…",
                        color="var(--vitta-text-muted)",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                min_height="13rem",
                width="100%",
                role="status",
                aria_live="polite",
            ),
            doctor_active_panel(),
        ),
        active_nav="clinical",
        page_title="Atendimento clínico",
        required_path="/medico",
    )


def finance_page() -> rx.Component:
    return dashboard_shell(
        Role.FINANCEIRO,
        "Financeiro",
        "O acesso financeiro está validado. Pagamentos, valores e operações com Asaas sandbox serão implementados em changes próprias.",
        active_nav="finance",
        required_path="/financeiro",
    )


def forbidden_page() -> rx.Component:
    """Render an authenticated 403-style route without disclosing another role's content."""
    content = rx.center(
        section_panel(
            rx.vstack(
                brand_logo(),
                rx.box(rx.icon("shield_x", size=25), class_name="vitta-empty-icon"),
                rx.text("403", class_name="vitta-eyebrow"),
                rx.heading("Acesso não autorizado", size="7", text_align="center"),
                rx.text(
                    "Sua sessão está ativa, mas esta área pertence a outra função da clínica.",
                    color="var(--vitta-text-muted)",
                    line_height="1.7",
                    text_align="center",
                    max_width="42ch",
                ),
                rx.button(
                    rx.hstack(rx.icon("arrow_left", size=17), rx.text("Voltar ao meu painel"), spacing="2"),
                    on_click=AuthState.go_to_dashboard,
                    class_name="vitta-primary-action",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            max_width="34rem",
        ),
        width="100%",
        min_height="100dvh",
        padding="1.25rem",
        background="var(--vitta-canvas)",
    )

    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role != ""),
        content,
        loading_surface(),
    )
