"""Vitta-One public, protected, and local QA page components."""

import reflex as rx

from vitta_one.appointment_scheduling.state import AdminAvailabilityState, ReceptionAgendaState
from vitta_one.auth.roles import Role
from vitta_one.ui.staff_components import admin_staff_panel
from vitta_one.ui.admin_hub_components import (
    admin_hub_workspace, admin_staff_type_workspace,
    admin_staff_create_workspace, admin_staff_detail_workspace,
)
from vitta_one.auth.state import AuthState
from vitta_one.doctor_workspace.state import DoctorWorkspaceState
from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
from vitta_one.patient_portal.state import PatientPortalState
from vitta_one.ui.patient_booking_components import patient_booking_workspace
from vitta_one.ui.patient_directory_components import (
    patient_directory_workspace, patient_create_workspace, patient_detail_workspace,
    patient_edit_workspace,
)
from vitta_one.professional_directory.state import AdminDirectoryState
from vitta_one.reception.dashboard.components import reception_dashboard
from vitta_one.ui.admin_directory_components import (
    admin_directory_workspace,
    professional_registration_workspace,
    specialties_management_workspace,
    professionals_management_workspace,
)
from vitta_one.ui.appointment_components import admin_availability_panel, reception_agenda_panel, reception_agenda_dialogs
from vitta_one.ui.admin_preview_components import (
    agenda_preview,
    clinical_preview,
    finance_preview,
    patients_preview,
    patient_detail_preview,
    reception_preview,
)
from vitta_one.ui.components import (
    admin_preview_workspace,
    brand_logo,
    breadcrumb,
    dashboard_shell,
    feedback_region,
    empty_state,
    loading_surface,
    login_form,
    page_header,
    protected_workspace,
    field_label,
    section_panel,
)
from vitta_one.ui.prescription_components import prescription_print_page
from vitta_one.ui.queue_components import (
    active_queue_panel,
    doctor_active_panel,
    doctor_waiting_summary,
    clinical_history_panel,
    enqueue_panel,
    queue_patient_picker,
    patient_identity_panel,
    reassess_panel,
    withdraw_panel,
)
from vitta_one.ui.workspace_components import (
    admin_clinic_configuration,
    doctor_calendar,
    doctor_week_calendar,
    doctor_consultation_list,
    doctor_patient_list,
    patient_calendar,
    patient_clinic_location,
    patient_consultation_list,
)


def root_page() -> rx.Component:
    """Render only a neutral routing surface while the session is resolved."""
    return loading_surface("Abrindo o Vitta-One…")


def login_page() -> rx.Component:
    """Prioritize authentication while preserving the Vitta One split layout."""
    content = rx.box(
        rx.box(
            brand_logo(width="10rem"),
            rx.box(
                rx.heading(
                    "Acesse sua conta",
                    font_size=rx.breakpoints(initial="2rem", sm="2.45rem"),
                    line_height="1.12",
                    letter_spacing="-0.035em",
                    font_family="var(--vitta-font-display)",
                    class_name="vitta-login-title",
                ),
                rx.text(
                    "Entre com seu e-mail e senha para continuar.",
                    color="var(--vitta-text-muted)",
                    line_height="1.6",
                    margin_top="0.7rem",
                    max_width="42ch",
                    class_name="vitta-login-lead",
                ),
                rx.box(login_form(), margin_top="1.75rem"),
                rx.text(
                    "Acesso exclusivo a usuários autorizados.",
                    color="var(--vitta-text-subtle)",
                    font_size="0.8rem",
                    margin_top="1.4rem",
                ),
                class_name="vitta-login-form-wrap",
            ),
            class_name="vitta-login-form-pane",
        ),
        rx.box(
            rx.box(
                rx.box(
                    rx.icon("activity", size=42),
                    class_name="vitta-login-emblem-icon",
                ),
                class_name="vitta-login-emblem",
            ),
            rx.box(
                rx.heading(
                    "Uma rotina clínica mais clara.",
                    font_size=rx.breakpoints(initial="2rem", lg="2.75rem"),
                    line_height="1.1",
                    letter_spacing="-0.035em",
                    color="#ffffff",
                    font_family="var(--vitta-font-display)",
                    max_width="14ch",
                ),
                rx.text(
                    "Agenda, atendimento e prontuário em um ambiente integrado.",
                    color="rgba(255,255,255,0.87)",
                    line_height="1.6",
                    max_width="40ch",
                    margin_top="0.95rem",
                ),
                class_name="vitta-login-caption",
            ),
            class_name="vitta-login-visual",
            aria_hidden="true",
        ),
        class_name="vitta-login-shell",
    )
    return rx.cond(
        AuthState.auth_checked & (AuthState.current_role == ""),
        content,
        loading_surface(),
    )


def patient_activation_page() -> rx.Component:
    """Public activation form posts directly to a native ASGI endpoint."""
    return rx.box(
        rx.vstack(
            brand_logo(width="9rem"),
            page_header(
                "Ativação de acesso",
                "Ative seu portal",
                "Use o código enviado pela Recepção e escolha uma senha para consultar suas próprias consultas.",
            ),
            section_panel(
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            field_label("E-mail do convite", "patient-activation-email"),
                            rx.el.input(
                                id="patient-activation-email",
                                name="email",
                                type="email",
                                auto_complete="email",
                                required=True,
                                max_length=320,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Código de ativação", "patient-activation-code"),
                            rx.el.input(
                                id="patient-activation-code",
                                name="code",
                                type="text",
                                auto_complete="one-time-code",
                                required=True,
                                max_length=128,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Nova senha", "patient-activation-password"),
                            rx.el.input(
                                id="patient-activation-password",
                                name="password",
                                type="password",
                                auto_complete="new-password",
                                required=True,
                                min_length=12,
                                max_length=128,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                            ),
                            width="100%",
                        ),
                        rx.text("Use pelo menos 12 caracteres. A senha não é enviada ao estado Reflex.", size="1", color="var(--vitta-text-muted)"),
                        rx.el.button(
                            "Ativar acesso",
                            type="button",
                            width="100%",
                            min_height="2.8rem",
                            padding="0.7rem 1.15rem",
                            border_radius="var(--vitta-radius-control)",
                            background="var(--vitta-primary)",
                            color="#fff",
                            font_weight="750",
                            class_name="vitta-primary-action",
                            on_click=rx.call_script(
                                "(() => { const form = document.getElementById('patient-activation-form'); if (form?.reportValidity()) form.submit(); })()"
                            ),
                        ),
                        spacing="4",
                        width="100%",
                        align="stretch",
                    ),
                    id="patient-activation-form",
                    action="/api/paciente/ativar",
                    method="post",
                    enc_type="application/x-www-form-urlencoded",
                    width="100%",
                )
            ),
            rx.link("Voltar ao login", href="/login", class_name="vitta-context-link"),
            spacing="5",
            width="100%",
            max_width="42rem",
            align="stretch",
            margin="0 auto",
        ),
        class_name="vitta-page",
        min_height="100vh",
        padding="2rem 1rem",
    )

def first_access_page() -> rx.Component:
    """Provisional doctors must rotate an initial password before clinical access."""
    content = rx.center(
        rx.box(
            rx.vstack(
                brand_logo(width="9rem"),
                rx.heading("Defina sua nova senha", size="7"),
                rx.text(
                    "Por segurança, escolha uma senha definitiva para continuar.",
                    color="var(--vitta-text-muted)", line_height="1.5",
                ),
                rx.el.form(
                    rx.vstack(
                        rx.box(
                            rx.el.label("Senha temporária", html_for="first-access-current"),
                            rx.el.input(
                                id="first-access-current", name="current_password",
                                type="password", required=True,
                                auto_complete="current-password", class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.box(
                            rx.el.label("Nova senha (mínimo 12 caracteres)",
                                        html_for="first-access-new"),
                            rx.el.input(
                                id="first-access-new", name="new_password",
                                type="password", required=True,
                                auto_complete="new-password", min_length=12,
                                class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.box(
                            rx.el.label("Confirme a nova senha",
                                        html_for="first-access-confirm"),
                            rx.el.input(
                                id="first-access-confirm", name="confirm_password",
                                type="password", required=True,
                                auto_complete="new-password", class_name="vitta-input",
                            ), width="100%",
                        ),
                        rx.cond(
                            AuthState.first_access_error != "",
                            rx.callout(
                                AuthState.first_access_error, color_scheme="red",
                                role="alert",
                            ),
                            rx.fragment(),
                        ),
                        rx.button(
                            "Salvar nova senha", type="submit", width="100%",
                            loading=AuthState.is_submitting,
                            disabled=AuthState.is_submitting,
                            color_scheme="teal", size="3",
                        ),
                        spacing="4", width="100%", align="stretch",
                    ),
                    on_submit=AuthState.save_first_access,
                    no_validate=True, width="100%",
                ),
                rx.button("Sair", type="button", variant="ghost",
                          on_click=AuthState.logout),
                spacing="4", width="100%", align="stretch",
            ),
            padding=rx.breakpoints(initial="1.25rem", sm="2rem"),
            width="100%", max_width="30rem",
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-panel)",
            background="var(--vitta-surface)",
        ),
        min_height="100dvh", width="100%", padding="1rem",
        background="var(--vitta-canvas)",
    )
    return rx.cond(
        AuthState.auth_checked
        & (AuthState.current_role == Role.MEDICO.value)
        & (AuthState.verified_path == "/primeiro-acesso"),
        content,
        loading_surface(),
    )


def admin_page() -> rx.Component:
    """Focused administration entry point; tools are in dedicated routes."""
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_hub_workspace(),
        active="administracao",
    )


def admin_staff_types_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_staff_type_workspace(),
        active="funcionarios",
        verified_path="/admin/funcionarios",
    )


def admin_staff_create_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_staff_create_workspace(),
        active="funcionarios",
        verified_path="/admin/funcionarios/novo",
    )


def admin_staff_detail_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        admin_staff_detail_workspace(),
        active="funcionarios",
        verified_path="/admin/funcionarios/[employee_id]",
    )


def admin_medical_staff_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        professional_registration_workspace(),
        active="funcionarios",
        verified_path="/admin/funcionarios/medico",
    )


def admin_receptionist_staff_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_header(
            "Administração / Funcionários",
            "Cadastrar recepcionista",
            "Defina as credenciais iniciais para uma conta de Recepção.",
        ),
        breadcrumb(("Administração", "/admin"), ("Funcionários", "/admin/funcionarios"),
                   ("Cadastrar recepcionista", None)),
        admin_staff_panel(),
        active="funcionarios",
        verified_path="/admin/funcionarios/recepcionista",
    )


def admin_hours_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_header(
            "Administração / Agenda",
            "Gerenciar horários",
            "Configure e consulte a disponibilidade dos médicos, uma tarefa por vez.",
        ),
        breadcrumb(("Administração", "/admin"), ("Horários", None)),
        admin_availability_panel(),
        active="horarios",
        verified_path="/admin/horarios",
    )


def admin_clinic_settings_page() -> rx.Component:
    return protected_workspace(
        Role.ADMINISTRADOR,
        page_header(
            "Administração",
            "Configurações da clínica",
            "Mantenha atualizadas as informações exibidas no portal do paciente.",
        ),
        breadcrumb(("Administração", "/admin"), ("Configurações", None)),
        admin_clinic_configuration(),
        active="configuracoes",
        verified_path="/admin/configuracoes",
    )


def admin_specialties_page() -> rx.Component:
    """Administrator-only full specialty directory."""
    return protected_workspace(
        Role.ADMINISTRADOR,
        specialties_management_workspace(),
        active="especialidades",
        verified_path="/admin/especialidades",
    )


def admin_professionals_page() -> rx.Component:
    """Administrator-only full professional directory."""
    return protected_workspace(
        Role.ADMINISTRADOR,
        professionals_management_workspace(),
        active="profissionais",
        verified_path="/admin/profissionais",
    )


def reception_page() -> rx.Component:
    """Reception's operational home; no patient clinical data is exposed here."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        reception_dashboard(),
        active="recepcao",
    )


def reception_agenda_page(verified_path: str = "/recepcao/agenda") -> rx.Component:
    """Scheduling, rescheduling, cancellation and check-in; preserved services."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        page_header(
            "Agenda",
            "Agenda e check-in",
            "Consulte a semana, localize consultas e confirme a chegada.",
            rx.button(
                rx.icon("calendar_plus", size=17),
                "Agendar consulta",
                type="button", color_scheme="teal", high_contrast=True,
                on_click=ReceptionAgendaState.open_booking,
                disabled=ReceptionAgendaState.is_submitting,
                class_name="vitta-primary-action",
            ),
        ),
        reception_agenda_panel(),
        active="agenda",
        verified_path="/recepcao/agenda",
    )


def reception_booking_page() -> rx.Component:
    """Compatibility route: show the canonical Agenda with its booking modal."""
    return reception_agenda_page(verified_path="/recepcao/agenda/nova")


def reception_patients_page() -> rx.Component:
    """Directory list and server-side search, separate from registration."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        patient_directory_workspace(),
        active="pacientes",
        verified_path="/recepcao/pacientes",
    )


def reception_patient_create_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        patient_create_workspace(),
        active="pacientes",
        verified_path="/recepcao/pacientes/novo",
    )


def reception_patient_detail_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        patient_detail_workspace(),
        active="pacientes",
        verified_path="/recepcao/pacientes/[patient_id]",
    )


def reception_patient_edit_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        patient_edit_workspace(),
        reception_agenda_dialogs(),
        active="pacientes",
        verified_path="/recepcao/pacientes/[patient_id]/editar",
    )


def reception_queue_new_page() -> rx.Component:
    return protected_workspace(
        Role.RECEPCIONISTA,
        breadcrumb(
            ("Recepção", "/recepcao"), ("Fila de espera", "/recepcao/fila"),
            ("Adicionar à fila", None),
        ),
        page_header(
            "Fila", "Adicionar à fila",
            "Selecione um paciente cadastrado e registre a prioridade informada.",
        ),
        rx.cond(
            ReceptionQueueState.selected_patient_id > 0,
            enqueue_panel(),
            queue_patient_picker(),
        ),
        active="fila",
        verified_path="/recepcao/fila/nova",
    )


def reception_queue_page() -> rx.Component:
    """An authorized, clinically ordered waiting queue for Reception."""
    return protected_workspace(
        Role.RECEPCIONISTA,
        breadcrumb(("Recepção", "/recepcao"), ("Fila de espera", None)),
        page_header(
            "Fila",
            "Fila de espera",
            "Acompanhe pacientes aguardando, prioridades e tempos de espera.",
            rx.link(
                rx.icon("plus", size=17),
                "Adicionar à fila",
                href="/recepcao/fila/nova",
                class_name="vitta-primary-action",
            ),
        ),
        active_queue_panel(),
        rx.cond(
            ReceptionQueueState.reassess_entry_id > 0,
            rx.dialog.root(
                rx.dialog.content(
                    reassess_panel(),
                    class_name="vitta-dialog-content", max_width="39rem",
                    max_height="85vh", overflow_y="auto",
                ),
                open=True,
            ),
            rx.fragment(),
        ),
        rx.cond(
            ReceptionQueueState.withdraw_entry_id > 0,
            rx.dialog.root(
                rx.dialog.content(
                    withdraw_panel(),
                    class_name="vitta-dialog-content", max_width="39rem",
                    max_height="85vh", overflow_y="auto",
                ),
                open=True,
            ),
            rx.fragment(),
        ),
        active="fila",
        verified_path="/recepcao/fila",
    )



def doctor_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Consultório médico",
            "Visão geral do consultório",
            "Acompanhe a agenda, o pronto-socorro, os pacientes e os registros clínicos.",
        ),
        rx.grid(
            rx.link(
                rx.vstack(
                    rx.icon("list_ordered", color="var(--vitta-primary)", size=21),
                    rx.heading(DoctorQueueState.waiting_count, size="6"),
                    rx.text("Pacientes na espera", size="2", font_weight="650"),
                    spacing="2", align="start",
                ),
                href="/medico", class_name="vitta-overview-card",
            ),
            rx.link(
                rx.vstack(
                    rx.icon("calendar_days", color="var(--vitta-primary)", size=21),
                    rx.heading(DoctorWorkspaceState.consultation_rows.length(), size="6"),
                    rx.text("Consultas no mês", size="2", font_weight="650"),
                    spacing="2", align="start",
                ),
                href="/medico/agenda", class_name="vitta-overview-card",
            ),
            rx.link(
                rx.vstack(
                    rx.icon("file_heart", color="var(--vitta-primary)", size=21),
                    rx.heading(rx.cond(DoctorQueueState.has_active, "Em andamento", "Sem atendimento"), size="4"),
                    rx.text("Prontuário atual", size="2", font_weight="650"),
                    spacing="2", align="start",
                ),
                href="/medico/prontuarios", class_name="vitta-overview-card",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            gap="3", width="100%",
        ),
        rx.flex(
            rx.link(rx.icon("calendar_days", size=17), "Abrir agenda",
                    href="/medico/agenda", class_name="vitta-context-link"),
            rx.link(rx.icon("users", size=17), "Meus pacientes",
                    href="/medico/pacientes", class_name="vitta-context-link"),
            rx.link(rx.icon("book_open", size=17), "Prontuário",
                    href="/medico/prontuarios", class_name="vitta-context-link"),
            gap="3", flex_wrap="wrap", align="center",
        ),
        rx.separator(),
        rx.heading("Operação de pronto-socorro", size="5"),
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
        active="atendimento",
    )


def doctor_records_page() -> rx.Component:
    """Active-patient records only: no unrestricted medical history browsing."""
    return protected_workspace(
        Role.MEDICO,
        breadcrumb(("Consultório", "/medico"), ("Prontuários", None)),
        page_header(
            "Prontuários", "Registro clínico do paciente atual",
            "Acesso restrito ao atendimento associado à sua sessão médica.",
        ),
        rx.cond(
            DoctorQueueState.has_active,
            clinical_history_panel(),
            section_panel(
                empty_state(
                    "clipboard_list", "Nenhum prontuário em atendimento",
                    "Chame o próximo paciente no pronto-socorro para acessar o registro associado.",
                    rx.link("Ir ao pronto-socorro", href="/medico",
                            class_name="vitta-context-link"),
                )
            ),
        ),
        active="prontuarios",
        verified_path="/medico/prontuarios",
    )


def doctor_agenda_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Agenda médica",
            "Minha agenda",
            "Consultas relacionadas ao profissional associado à sua conta, com datas no fuso da clínica.",
        ),
        feedback_region(DoctorWorkspaceState.error_message, "", "doctor-agenda-feedback"),
        rx.link("Abrir fila e atendimento clínico", href="/medico", class_name="vitta-context-link"),
        doctor_week_calendar(),
        rx.heading("Calendário do mês", size="5"),
        doctor_calendar(),
        doctor_consultation_list(),
        active="agenda-medica",
        verified_path="/medico/agenda",
    )


def doctor_patients_page() -> rx.Component:
    return protected_workspace(
        Role.MEDICO,
        page_header(
            "Pacientes",
            "Pacientes vinculados",
            "Pessoas derivadas exclusivamente de consultas do seu cadastro profissional.",
        ),
        feedback_region(DoctorWorkspaceState.error_message, "", "doctor-patients-feedback"),
        doctor_patient_list(),
        active="pacientes-medico",
        verified_path="/medico/pacientes",
    )


def patient_booking_page() -> rx.Component:
    """Self-service booking, always scoped to the patient session."""
    return protected_workspace(
        Role.PACIENTE,
        page_header(
            "Agenda",
            "Agendar consulta",
            "Encontre uma especialidade, escolha o médico e reserve seu horário.",
            rx.link("Voltar às minhas consultas", href="/paciente",
                    class_name="vitta-context-link"),
        ),
        patient_booking_workspace(),
        active="agendar-paciente",
        verified_path="/paciente/agendar",
    )


def patient_portal_page() -> rx.Component:
    return protected_workspace(
        Role.PACIENTE,
        page_header(
            "Minhas consultas",
            "Agenda do paciente",
            "Consulte compromissos futuros e passados vinculados à sua conta.",
            rx.link(
                rx.button(
                    rx.icon("calendar_plus", size=17),
                    "Agendar nova consulta",
                    color_scheme="teal", high_contrast=True,
                    min_height="2.75rem",
                ),
                href="/paciente/agendar",
            ),
        ),
        feedback_region(PatientPortalState.error_message, "", "patient-portal-feedback"),
        patient_clinic_location(),
        patient_calendar(),
        patient_consultation_list(),
        active="consultas-paciente",
        verified_path="/paciente",
    )


def finance_page() -> rx.Component:
    return dashboard_shell(
        Role.FINANCEIRO,
        "Financeiro",
        "O acesso financeiro está validado. Pagamentos, valores e integração com Asaas sandbox serão implementados em change própria.",
    )


def admin_reception_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/recepcao",
        "recepcao",
        reception_preview(),
    )


def admin_agenda_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/agenda",
        "agenda",
        agenda_preview(),
    )


def admin_clinical_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/atendimento",
        "atendimento",
        clinical_preview(),
    )


def admin_patients_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/pacientes",
        "pacientes",
        patients_preview(),
    )


def admin_patient_detail_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/pacientes/[patient_id]",
        "pacientes",
        patient_detail_preview(),
    )


def admin_finance_preview_page() -> rx.Component:
    return admin_preview_workspace(
        "/admin/financeiro",
        "financeiro",
        finance_preview(),
    )


def forbidden_page() -> rx.Component:
    """Render an authenticated 403-style route without disclosing another role's content."""
    content = rx.center(
        rx.box(
            brand_logo(width="8.5rem"),
            rx.box(
                rx.text(
                    "403 · ACESSO RESTRITO",
                    font_size="0.72rem",
                    font_weight="800",
                    letter_spacing="0.09em",
                    color="var(--vitta-primary)",
                ),
                rx.heading(
                    "Esta área pertence a outra função.",
                    size="8",
                    letter_spacing="-0.035em",
                    font_family="var(--vitta-font-display)",
                    margin_top="0.6rem",
                ),
                rx.text(
                    "Sua sessão continua ativa. Volte ao ambiente compatível com sua função para continuar.",
                    color="var(--vitta-text-muted)",
                    line_height="1.65",
                    max_width="46ch",
                    margin_top="0.7rem",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("arrow_left", size=17),
                        rx.text("Voltar ao meu painel"),
                        spacing="2",
                        align="center",
                    ),
                    size="3",
                    color_scheme="teal",
                    high_contrast=True,
                    on_click=AuthState.go_to_dashboard,
                    margin_top="1.4rem",
                ),
                margin_top="1.5rem",
            ),
            width="min(100%, 37rem)",
            padding=rx.breakpoints(initial="1.5rem", sm="2.25rem"),
            border="1px solid var(--vitta-border)",
            border_radius="var(--vitta-radius-large)",
            background="var(--vitta-surface)",
            box_shadow="var(--vitta-shadow-sm)",
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
