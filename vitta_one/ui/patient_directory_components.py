"""Focused patient directory, onboarding and detail surfaces for Reception."""
import reflex as rx

from vitta_one.patient_queue.state import ReceptionQueueState as S
from vitta_one.ui.components import breadcrumb, feedback_region, field_label, page_header, section_panel
from vitta_one.ui.queue_components import (
    selected_patient_operations, patient_selection_summary,
)


def _patient_row(row) -> rx.Component:
    return rx.link(
        rx.flex(
            rx.hstack(
                rx.box(rx.icon("user_round", size=20), class_name="vitta-admin-action-icon"),
                rx.vstack(
                    rx.text(row["name"], font_weight="750", color="var(--vitta-text)"),
                    rx.text(row["phone"], color="var(--vitta-text-muted)", size="2"),
                    spacing="1", align="start",
                ),
                gap="3", align="center",
            ),
            rx.icon("chevron_right", size=18, color="var(--vitta-text-muted)"),
            gap="3", align="center", justify="between", width="100%",
        ),
        href=row["href"].to(str),
        class_name="vitta-staff-row",
    )


def patient_directory_workspace() -> rx.Component:
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", None)),
        page_header(
            "Pacientes", "Lista de pacientes",
            "Pesquise os registros da clínica. Cadastros novos têm uma tela própria.",
            rx.link(rx.icon("user_plus", size=17), "Novo paciente",
                    href="/recepcao/pacientes/novo", class_name="vitta-primary-action"),
        ),
        section_panel(
            rx.vstack(
                rx.el.form(
                    rx.flex(
                        rx.box(
                            field_label("Pesquisar pacientes", "patient-directory-search"),
                            rx.el.input(
                                id="patient-directory-search", type="search",
                                name="query", placeholder="Nome ou CPF",
                                auto_complete="off", max_length=100,
                                class_name="vitta-input",
                                value=S.patient_directory_query,
                                on_change=S.update_patient_directory_query,
                            ),
                            width="100%", flex="1",
                        ),
                        rx.button(rx.icon("search", size=17), "Buscar",
                                  type="submit", color_scheme="teal", high_contrast=True,
                                  disabled=S.patient_directory_loading),
                        align="end", gap="3", width="100%", flex_wrap="wrap",
                    ),
                    on_submit=S.search_patient_directory, width="100%",
                ),
                rx.cond(
                    S.patient_directory_loading,
                    rx.center(rx.spinner(size="3"), min_height="9rem", width="100%"),
                    rx.cond(
                        S.patient_directory.length() > 0,
                        rx.vstack(rx.foreach(S.patient_directory, _patient_row),
                                  spacing="2", width="100%", align="stretch"),
                        rx.center(rx.vstack(
                            rx.icon("users", color="var(--vitta-primary)", size=26),
                            rx.heading("Nenhum paciente encontrado", size="4"),
                            rx.text("Tente outra busca ou registre o primeiro paciente.",
                                    color="var(--vitta-text-muted)", size="2"),
                            rx.link("Novo paciente", href="/recepcao/pacientes/novo",
                                    class_name="vitta-context-link"),
                            align="center", spacing="3"),
                            min_height="13rem", width="100%"),
                    ),
                ),
                rx.flex(
                    rx.text(S.patient_directory_total, " pacientes",
                            size="2", color="var(--vitta-text-muted)"),
                    rx.hstack(
                        rx.button("Anterior", variant="outline", color_scheme="teal",
                                  on_click=S.move_patient_directory_page(-1),
                                  disabled=S.patient_directory_page <= 1),
                        rx.text(S.patient_directory_page_label,
                                font_weight="650", size="2"),
                        rx.button("Próxima", variant="outline", color_scheme="teal",
                                  on_click=S.move_patient_directory_page(1),
                                  disabled=S.patient_directory_page >= S.patient_directory_pages),
                        gap="3", align="center",
                    ),
                    justify="between", gap="3", align="center", flex_wrap="wrap",
                    width="100%",
                ),
                spacing="5", width="100%", align="stretch",
            )
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


def patient_detail_workspace() -> rx.Component:
    """Read-only patient summary; editing and booking use dedicated routes."""
    return rx.vstack(
        breadcrumb(("Recepção", "/recepcao"), ("Pacientes", "/recepcao/pacientes"),
                   ("Ficha do paciente", None)),
        page_header(
            "Pacientes", "Ficha do paciente",
            "Dados de identificação e atalhos para as operações deste cadastro.",
        ),
        section_panel(
            rx.vstack(
                rx.flex(
                    rx.box(
                        rx.icon("user_round", size=28, color="var(--vitta-primary)"),
                        class_name="vitta-patient-profile-mark",
                    ),
                    rx.vstack(
                        rx.text("PACIENTE", class_name="vitta-section-kicker"),
                        rx.heading(S.selected_patient_name, size="6"),
                        rx.text("Cadastro #", S.selected_patient_id,
                                color="var(--vitta-text-muted)", size="2"),
                        spacing="2", align="start", flex="1", min_width="0",
                    ),
                    align="center", gap="4", width="100%",
                ),
                rx.separator(),
                rx.box(
                    rx.text("Contato", font_weight="700", color="var(--vitta-text)", size="2"),
                    rx.hstack(
                        rx.icon("phone", size=16, color="var(--vitta-primary)"),
                        rx.text(S.selected_patient_phone, size="3"),
                        align="center", spacing="2", margin_top="0.4rem",
                    ),
                ),
                rx.separator(),
                rx.text(
                    "Escolha uma operação",
                    font_weight="700", color="var(--vitta-text)", size="3",
                ),
                rx.flex(
                    rx.button(
                        rx.icon("calendar_plus", size=17), "Agendar consulta",
                        color_scheme="teal", high_contrast=True,
                        on_click=S.open_selected_patient_agenda,
                    ),
                    rx.link(
                        rx.hstack(rx.icon("list_ordered", size=17),
                                  rx.text("Adicionar à fila"), spacing="2", align="center"),
                        href="/recepcao/fila/nova", class_name="vitta-context-link",
                    ),
                    rx.link(
                        rx.hstack(rx.icon("settings_2", size=17),
                                  rx.text("Editar dados e acesso"), spacing="2", align="center"),
                        href="/recepcao/pacientes/" + S.selected_patient_id.to(str) + "/editar",
                        class_name="vitta-context-link",
                    ),
                    gap="3", flex_wrap="wrap", align="center",
                    width="100%", class_name="vitta-patient-profile-actions",
                ),
                spacing="5", align="stretch", width="100%",
                class_name="vitta-patient-profile",
            ),
        ),
        align="stretch", spacing="5", width="100%",
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
