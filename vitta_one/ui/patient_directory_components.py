"""Focused patient directory, onboarding and detail surfaces for Reception."""
import reflex as rx

from vitta_one.patient_queue.state import ReceptionQueueState as S
from vitta_one.ui.appointment_components import consultation_status_badge, reception_agenda_dialogs
from vitta_one.ui.components import breadcrumb, feedback_region, field_label, page_header, section_panel
from vitta_one.ui.queue_components import (
    selected_patient_operations, patient_selection_summary,
)


def _patient_row(row) -> rx.Component:
    """One semantic table row, with an explicit patient-detail action."""
    return rx.el.tr(
        rx.el.td(
            rx.text(
                row["name"], font_weight="700", color="var(--vitta-text)",
                overflow_wrap="anywhere",
            ),
            rx.text(
                row["phone"], size="1", color="var(--vitta-text-muted)",
                class_name="vitta-patient-directory-mobile-phone",
                overflow_wrap="anywhere",
            ),
            data_label="Paciente",
        ),
        rx.el.td(
            rx.text(row["phone"], size="2", overflow_wrap="anywhere"),
            data_label="Telefone",
            class_name="vitta-patient-directory-phone-column",
        ),
        rx.el.td(
            rx.link(
                "Ver detalhes",
                href=row["href"].to(str),
                aria_label="Ver detalhes de " + row["name"],
                class_name="vitta-context-link vitta-patient-directory-detail",
            ),
            data_label="Ações",
            class_name="vitta-patient-directory-action-column",
        ),
        class_name="vitta-patient-directory-row",
    )


def _patient_directory_table() -> rx.Component:
    return rx.el.table(
        rx.el.thead(
            rx.el.tr(
                rx.el.th("Paciente", scope="col"),
                rx.el.th(
                    "Telefone", scope="col",
                    class_name="vitta-patient-directory-phone-column",
                ),
                rx.el.th("Ações", scope="col", class_name="vitta-patient-directory-action-column"),
            )
        ),
        rx.el.tbody(rx.foreach(S.patient_directory, _patient_row)),
        class_name="vitta-patient-directory-table",
    )


def _patient_directory_empty() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon("users", color="var(--vitta-primary)", size=24),
            rx.heading(
                rx.cond(
                    S.patient_directory_applied_query != "",
                    "Nenhum paciente corresponde à pesquisa.",
                    "Nenhum paciente cadastrado.",
                ),
                size="4",
            ),
            rx.text(
                rx.cond(
                    S.patient_directory_applied_query != "",
                    "Revise os termos ou limpe a pesquisa.",
                    "Cadastre um paciente para começar.",
                ),
                size="2", color="var(--vitta-text-muted)",
            ),
            rx.cond(
                S.patient_directory_applied_query != "",
                rx.button(
                    "Limpar pesquisa", type="button",
                    variant="outline", color_scheme="teal",
                    on_click=S.clear_patient_directory_search,
                ),
                rx.link(
                    "Novo paciente", href="/recepcao/pacientes/novo",
                    class_name="vitta-context-link",
                ),
            ),
            spacing="3", align="center", text_align="center",
        ),
        min_height="10rem", width="100%",
    )


def patient_directory_workspace() -> rx.Component:
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", None)),
        page_header(
            "Pacientes", "Lista de pacientes",
            "Localize pacientes cadastrados e consulte suas informações.",
            rx.link(
                rx.hstack(
                    rx.icon("user_plus", size=17, flex_shrink="0"),
                    rx.text("Novo paciente"),
                    spacing="2", align="center",
                ),
                href="/recepcao/pacientes/novo",
                class_name="vitta-primary-action vitta-patient-directory-new",
            ),
        ),
        section_panel(
            rx.vstack(
                rx.el.form(
                    rx.flex(
                        rx.box(
                            field_label("Pesquisar pacientes", "patient-directory-search"),
                            rx.el.input(
                                id="patient-directory-search", type="search",
                                name="query", placeholder="Nome, CPF ou telefone",
                                auto_complete="off", max_length=100,
                                class_name="vitta-input",
                                margin_top="0.4rem",
                                value=S.patient_directory_query,
                                on_change=S.update_patient_directory_query,
                                aria_describedby="patient-directory-search-help",
                            ),
                            rx.text(
                                "A pesquisa considera nome, CPF e telefone dos cadastros autorizados.",
                                id="patient-directory-search-help",
                                size="1", margin_top="0.4rem",
                                color="var(--vitta-text-muted)",
                            ),
                            width="100%", flex="1", min_width="0",
                        ),
                        rx.hstack(
                            rx.button(
                                rx.icon("search", size=17), "Buscar",
                                type="submit", color_scheme="teal",
                                high_contrast=True,
                                disabled=S.patient_directory_loading,
                            ),
                            rx.button(
                                "Limpar", type="button",
                                variant="outline", color_scheme="teal",
                                on_click=S.clear_patient_directory_search,
                                disabled=S.patient_directory_loading | (S.patient_directory_query == ""),
                            ),
                            spacing="2", align="center", flex_wrap="wrap",
                        ),
                        align="end", gap="3", width="100%",
                        direction=rx.breakpoints(initial="column", sm="row"),
                    ),
                    on_submit=S.search_patient_directory,
                    width="100%",
                ),
                rx.cond(
                    S.patient_directory_loading,
                    rx.center(
                        rx.hstack(
                            rx.spinner(size="3"),
                            rx.text("Carregando pacientes…", size="2"),
                            spacing="3", align="center",
                        ),
                        min_height="8rem", width="100%",
                        role="status", aria_live="polite",
                    ),
                    rx.cond(
                        S.patient_directory_error != "",
                        rx.vstack(
                            rx.text(
                                S.patient_directory_error,
                                role="alert", color="var(--vitta-danger)",
                            ),
                            rx.button(
                                "Tentar novamente", type="button",
                                variant="outline", color_scheme="teal",
                                on_click=S.load_patient_list,
                            ),
                            align="start", spacing="3",
                            width="100%", padding="1rem 0",
                        ),
                        rx.cond(
                            S.patient_directory.length() > 0,
                            _patient_directory_table(),
                            _patient_directory_empty(),
                        ),
                    ),
                ),
                rx.cond(
                    (S.patient_directory_error == "") & ~S.patient_directory_loading,
                    rx.flex(
                        rx.text(
                            S.patient_directory_total,
                            rx.cond(
                                S.patient_directory_total == 1,
                                " paciente encontrado",
                                " pacientes encontrados",
                            ),
                            size="2", color="var(--vitta-text-muted)",
                            role="status", aria_live="polite",
                        ),
                        rx.cond(
                            S.patient_directory_pages > 1,
                            rx.hstack(
                                rx.button(
                                    "Anterior", type="button",
                                    variant="outline", color_scheme="teal",
                                    on_click=S.move_patient_directory_page(-1),
                                    disabled=S.patient_directory_page <= 1,
                                ),
                                rx.text(
                                    S.patient_directory_page_label,
                                    font_weight="650", size="2",
                                ),
                                rx.button(
                                    "Próxima", type="button",
                                    variant="outline", color_scheme="teal",
                                    on_click=S.move_patient_directory_page(1),
                                    disabled=S.patient_directory_page >= S.patient_directory_pages,
                                ),
                                gap="2", align="center",
                            ),
                            rx.fragment(),
                        ),
                        justify="between", gap="3", align="center",
                        flex_wrap="wrap", width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="4", width="100%", align="stretch",
            ),
        ),
        spacing="4", align="stretch", width="100%",
    )


def patient_create_workspace() -> rx.Component:
    """Compact registration form with server-owned validation and recovery."""
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", "/recepcao/pacientes"),
                   ("Novo paciente", None)),
        page_header(
            "Pacientes", "Novo paciente",
            "Cadastre os dados básicos do paciente. Após salvar, você será direcionado à ficha.",
        ),
        rx.box(
            section_panel(
                rx.el.form(
                    rx.vstack(
                        rx.heading("Dados pessoais", size="4", color="var(--vitta-text)"),
                        rx.text("Campos marcados com * são obrigatórios.",
                                size="2", color="var(--vitta-text-muted)"),
                        feedback_region(
                            S.error_message, S.success_message,
                            element_id="patient-create-feedback",
                        ),
                        rx.box(
                            field_label("Nome completo *", "patient-create-name"),
                            rx.el.input(
                                id="patient-create-name", name="name", type="text",
                                auto_complete="name", required=True, max_length=160,
                                placeholder="Nome completo do paciente",
                                class_name="vitta-input", margin_top="0.45rem",
                                value=S.new_patient_name,
                                on_change=S.update_new_patient_name,
                                disabled=S.is_submitting,
                                aria_invalid=S.new_patient_name_error != "",
                                aria_describedby="patient-create-name-error",
                            ),
                            rx.text(
                                S.new_patient_name_error,
                                id="patient-create-name-error", role="alert",
                                color="var(--vitta-danger)", size="2",
                                margin_top="0.35rem",
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("CPF *", "patient-create-cpf"),
                            rx.el.input(
                                id="patient-create-cpf", name="cpf", type="text",
                                input_mode="numeric", auto_complete="off",
                                required=True, max_length=14,
                                placeholder="000.000.000-00",
                                class_name="vitta-input", margin_top="0.45rem",
                                value=S.new_patient_cpf,
                                on_change=S.update_new_patient_cpf,
                                disabled=S.is_submitting,
                                aria_invalid=S.new_patient_cpf_error != "",
                                aria_describedby="patient-create-cpf-help patient-create-cpf-error",
                            ),
                            rx.text(
                                "Digite os 11 números do CPF. A formatação será aplicada automaticamente.",
                                id="patient-create-cpf-help", size="2",
                                color="var(--vitta-text-muted)", margin_top="0.4rem",
                            ),
                            rx.text(
                                S.new_patient_cpf_error,
                                id="patient-create-cpf-error", role="alert",
                                color="var(--vitta-danger)", size="2",
                                margin_top="0.3rem",
                            ),
                            rx.cond(
                                S.new_patient_duplicate_id > 0,
                                rx.link(
                                    "Abrir ficha existente",
                                    href="/recepcao/pacientes/" + S.new_patient_duplicate_id.to(str),
                                    class_name="vitta-context-link",
                                    margin_top="0.6rem",
                                ),
                                rx.fragment(),
                            ),
                            width="100%",
                        ),
                        rx.box(
                            field_label("Telefone (opcional)", "patient-create-phone"),
                            rx.el.input(
                                id="patient-create-phone", name="phone", type="tel",
                                input_mode="numeric", auto_complete="tel",
                                max_length=15, placeholder="(11) 99999-9999",
                                class_name="vitta-input", margin_top="0.45rem",
                                value=S.new_patient_phone,
                                on_change=S.update_new_patient_phone,
                                disabled=S.is_submitting,
                                aria_invalid=S.new_patient_phone_error != "",
                                aria_describedby="patient-create-phone-error",
                            ),
                            rx.text(
                                S.new_patient_phone_error,
                                id="patient-create-phone-error", role="alert",
                                color="var(--vitta-danger)", size="2",
                                margin_top="0.35rem",
                            ),
                            width="100%",
                        ),
                        rx.cond(
                            S.new_patient_created_id > 0,
                            rx.link(
                                "Abrir ficha do paciente cadastrado",
                                href="/recepcao/pacientes/" + S.new_patient_created_id.to(str),
                                class_name="vitta-context-link",
                            ),
                            rx.fragment(),
                        ),
                        rx.flex(
                            rx.link(
                                "Cancelar", href="/recepcao/pacientes",
                                class_name="vitta-context-link",
                            ),
                            rx.button(
                                "Cadastrar paciente", type="submit",
                                color_scheme="teal", high_contrast=True,
                                disabled=S.is_submitting | (S.new_patient_created_id > 0),
                                loading=S.is_submitting,
                            ),
                            align="center", justify="end", gap="3",
                            flex_wrap="wrap", width="100%",
                            class_name="vitta-patient-create-actions",
                        ),
                        spacing="4", align="stretch", width="100%",
                        class_name="vitta-form-panel",
                    ),
                    on_submit=S.create_patient,
                    no_validate=True, width="100%",
                ),
            ),
            max_width="44rem", width="100%",
        ),
        spacing="4", align="stretch", width="100%",
    )


def _operational_value(label: str, value) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", color="var(--vitta-text-muted)", font_weight="650"),
        rx.text(value, font_weight="650", overflow_wrap="anywhere", size="3"),
        spacing="1", align="start", min_width="0",
    )


def _patient_consultation_row(row) -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.text(row["scheduled_at"], font_weight="700",
                    class_name="vitta-tabular", size="2"),
            rx.text(row["professional_name"], size="2", overflow_wrap="anywhere"),
            spacing="1", align="start", min_width="0",
        ),
        consultation_status_badge(row["status"], row["status_label"]),
        align=rx.breakpoints(initial="start", sm="center"),
        direction=rx.breakpoints(initial="column", sm="row"),
        justify="between", gap="2", width="100%",
        padding_y="0.7rem",
        border_bottom="1px solid var(--vitta-border)",
    )


def _patient_queue_history_row(row) -> rx.Component:
    return rx.flex(
        rx.vstack(
            rx.text(row["entered_at"], font_weight="650",
                    class_name="vitta-tabular", size="2"),
            rx.text("Prioridade: ", row["priority_label"], size="2",
                    color="var(--vitta-text-muted)"),
            spacing="1", align="start",
        ),
        rx.badge(row["status_label"], variant="soft", color_scheme="gray"),
        align=rx.breakpoints(initial="start", sm="center"),
        justify="between", flex_wrap="wrap", gap="2",
        padding_y="0.65rem", width="100%",
        border_bottom="1px solid var(--vitta-border)",
    )


def _patient_detail_sections() -> rx.Component:
    edit_href = "/recepcao/pacientes/" + S.selected_patient_id.to(str) + "/editar"
    return rx.vstack(
        section_panel(
            rx.vstack(
                rx.flex(
                    rx.box(rx.icon("user_round", size=26,
                                   color="var(--vitta-primary)"),
                           class_name="vitta-patient-profile-mark"),
                    rx.vstack(
                        rx.text("IDENTIFICAÇÃO", class_name="vitta-section-kicker"),
                        rx.heading(S.selected_patient_name, size="6",
                                   overflow_wrap="anywhere"),
                        spacing="1", align="start", min_width="0",
                    ),
                    align="center", gap="3", width="100%",
                ),
                rx.separator(),
                rx.heading("Dados cadastrais", size="4"),
                rx.grid(
                    _operational_value("Nome completo", S.selected_patient_name),
                    _operational_value("CPF", S.selected_patient_cpf_masked),
                    _operational_value(
                        "Telefone",
                        rx.cond(S.selected_patient_phone != "",
                                S.selected_patient_phone, "Não informado"),
                    ),
                    columns=rx.breakpoints(initial="1", md="3"),
                    gap="4", width="100%",
                ),
                rx.link("Editar cadastro", href=edit_href,
                        class_name="vitta-context-link"),
                spacing="4", align="stretch", width="100%",
            ),
        ),
        rx.grid(
            section_panel(
                rx.vstack(
                    rx.heading("Próximas consultas", size="4"),
                    rx.cond(
                        S.patient_upcoming_consultations.length() > 0,
                        rx.vstack(
                            rx.foreach(S.patient_upcoming_consultations,
                                       _patient_consultation_row),
                            spacing="0", width="100%", align="stretch",
                        ),
                        rx.box(
                            rx.text("Nenhuma consulta futura", font_weight="700"),
                            rx.text(
                                "Este paciente não possui consultas futuras cadastradas.",
                                size="2", color="var(--vitta-text-muted)",
                                margin_top="0.3rem",
                            ),
                            class_name="vitta-info-strip", width="100%",
                        ),
                    ),
                    spacing="3", align="stretch", width="100%",
                )
            ),
            section_panel(
                rx.vstack(
                    rx.heading("Situação na fila", size="4"),
                    rx.cond(
                        S.patient_has_active_entry,
                        rx.vstack(
                            _operational_value(
                                "Situação", S.patient_active_entry["status_label"]
                            ),
                            _operational_value(
                                "Prioridade", S.patient_active_entry["priority_label"]
                            ),
                            _operational_value(
                                "Entrada", S.patient_active_entry["entered_at"]
                            ),
                            rx.link("Consultar fila de espera",
                                    href="/recepcao/fila",
                                    class_name="vitta-context-link"),
                            spacing="3", align="stretch",
                            width="100%", role="status",
                        ),
                        rx.vstack(
                            rx.text("Paciente sem entrada ativa na fila.",
                                    color="var(--vitta-text-muted)", size="2"),
                            rx.link("Adicionar à fila", href="/recepcao/fila/nova",
                                    class_name="vitta-context-link"),
                            spacing="3", align="start",
                        ),
                    ),
                    spacing="3", align="stretch", width="100%",
                )
            ),
            columns=rx.breakpoints(initial="1", lg="minmax(0, 1.4fr) minmax(0, 1fr)"),
            gap="4", width="100%",
        ),
        section_panel(
            rx.vstack(
                rx.heading("Histórico operacional", size="4"),
                rx.text(
                    "Somente datas, profissionais e situações. Dados clínicos não são exibidos.",
                    size="2", color="var(--vitta-text-muted)",
                ),
                rx.heading("Consultas anteriores e cancelamentos", size="3"),
                rx.cond(
                    S.patient_history_consultations.length() > 0,
                    rx.vstack(
                        rx.foreach(S.patient_history_consultations,
                                   _patient_consultation_row),
                        spacing="0", width="100%", align="stretch",
                    ),
                    rx.text("Nenhuma consulta anterior registrada.",
                            size="2", color="var(--vitta-text-muted)"),
                ),
                rx.cond(
                    S.patient_history_total > 6,
                    rx.flex(
                        rx.text("Página ", S.patient_history_page,
                                " de ", S.patient_history_pages,
                                size="2", color="var(--vitta-text-muted)"),
                        rx.hstack(
                            rx.button(
                                "Anterior", variant="outline", color_scheme="teal",
                                on_click=S.change_patient_history_page(-1),
                                disabled=S.patient_history_page <= 1,
                            ),
                            rx.button(
                                "Próxima", variant="outline", color_scheme="teal",
                                on_click=S.change_patient_history_page(1),
                                disabled=S.patient_history_page >= S.patient_history_pages,
                            ),
                            spacing="2",
                        ),
                        align="center", justify="between",
                        flex_wrap="wrap", gap="3", width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.separator(),
                rx.heading("Últimas movimentações na fila", size="3"),
                rx.cond(
                    S.patient_queue_history.length() > 0,
                    rx.vstack(
                        rx.foreach(S.patient_queue_history, _patient_queue_history_row),
                        align="stretch", spacing="0", width="100%",
                    ),
                    rx.text("Nenhuma movimentação anterior registrada.",
                            size="2", color="var(--vitta-text-muted)"),
                ),
                spacing="3", align="stretch", width="100%",
            )
        ),
        section_panel(
            rx.flex(
                rx.vstack(
                    rx.heading("Acesso ao portal", size="4"),
                    rx.text(S.selected_patient_portal_status,
                            role="status", aria_live="polite",
                            font_weight="650", size="2"),
                    rx.text(
                        "A situação exibida vem do vínculo e dos convites registrados.",
                        color="var(--vitta-text-muted)", size="2",
                    ),
                    align="start", spacing="2", min_width="0",
                ),
                rx.link("Gerenciar acesso ao portal", href=edit_href,
                        class_name="vitta-context-link"),
                align=rx.breakpoints(initial="start", sm="center"),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between", gap="3", width="100%",
            ),
        ),
        spacing="4", align="stretch", width="100%",
    )


def patient_detail_workspace() -> rx.Component:
    """Authorized operational patient hub with the shared reception booking flow."""
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", "/recepcao/pacientes"),
                   ("Ficha do paciente", None)),
        page_header(
            "Pacientes", "Ficha do paciente",
            "Identificação, consultas, fila e acesso operacional em um único lugar.",
            rx.button(
                rx.icon("calendar_plus", size=17), "Agendar consulta",
                type="button", color_scheme="teal", high_contrast=True,
                on_click=S.open_selected_patient_agenda,
                disabled=S.patient_detail_loading | ~S.patient_detail_loaded,
            ),
        ),
        rx.cond(
            S.patient_detail_loading,
            rx.center(rx.spinner(size="3"), min_height="10rem", width="100%",
                      role="status", aria_label="Carregando ficha do paciente"),
            rx.cond(
                S.patient_detail_loaded,
                _patient_detail_sections(),
                section_panel(
                    rx.vstack(
                        rx.heading("Ficha indisponível", size="4"),
                        rx.text(
                            rx.cond(S.patient_detail_error != "",
                                    S.patient_detail_error, "Paciente não encontrado."),
                            role="alert",
                        ),
                        rx.link("Voltar aos pacientes", href="/recepcao/pacientes",
                                class_name="vitta-context-link"),
                        rx.button(
                            "Tentar novamente", variant="outline",
                            color_scheme="teal", on_click=S.load_patient_detail,
                        ),
                        spacing="3", align="start",
                    ),
                ),
            ),
        ),
        reception_agenda_dialogs(),
        align="stretch", spacing="4", width="100%",
    )


def patient_edit_workspace() -> rx.Component:
    """Separate editable patient and portal configuration, never buried in a modal."""
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", "/recepcao/pacientes"),
                   ("Editar cadastro", None)),
        page_header("Pacientes", "Editar cadastro e acesso",
                    "Atualize a identificação e gerencie o portal com consentimento."),
        rx.link("Voltar à ficha",
                href="/recepcao/pacientes/" + S.selected_patient_id.to(str),
                class_name="vitta-context-link"),
        selected_patient_operations(),
        spacing="5", width="100%", align="stretch",
    )
