"""Premium read-only screens for the explicitly enabled local Administrator QA mode."""

import reflex as rx

from vitta_one.admin_preview.state import AdminPreviewState
from vitta_one.ui.components import (
    empty_state,
    error_banner,
    metric_card,
    page_header,
    section_panel,
)


def _priority_badge(priority, label) -> rx.Component:
    return rx.cond(
        priority == "VERMELHO",
        rx.badge(label, color_scheme="red", variant="soft", high_contrast=True),
        rx.cond(
            priority == "AMARELO",
            rx.badge(label, color_scheme="amber", variant="soft", high_contrast=True),
            rx.badge(label, color_scheme="green", variant="soft", high_contrast=True),
        ),
    )


def _status_badge(status, label) -> rx.Component:
    return rx.cond(
        status == "AGUARDANDO",
        rx.badge(label, color_scheme="blue", variant="soft", high_contrast=True),
        rx.cond(
            status == "EM_ATENDIMENTO",
            rx.badge(label, color_scheme="amber", variant="soft", high_contrast=True),
            rx.cond(
                status == "FINALIZADO",
                rx.badge(label, color_scheme="green", variant="soft", high_contrast=True),
                rx.badge(label, color_scheme="gray", variant="soft", high_contrast=True),
            ),
        ),
    )


def _preview_notice() -> rx.Component:
    return rx.hstack(
        rx.icon("monitor_cog", size=16),
        rx.text(
            "Visualização local somente leitura — as permissões reais de cada role continuam intactas.",
            size="2",
            line_height="1.5",
        ),
        spacing="2",
        align="start",
        width="100%",
        padding="0.8rem 0.9rem",
        border="1px solid var(--vitta-border)",
        border_radius="var(--vitta-radius-control)",
        background="var(--vitta-surface-subtle)",
        color="var(--vitta-text-muted)",
    )


def _queue_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["patient_name"], font_weight="750", size="2"),
                rx.text(
                    row["entered_at"],
                    font_size="0.74rem",
                    color="var(--vitta-text-subtle)",
                    margin_top="0.2rem",
                    class_name="vitta-tabular",
                ),
                min_width="0",
                flex="1 1 12rem",
            ),
            rx.hstack(
                _priority_badge(row["priority"], row["priority_label"]),
                _status_badge(row["status"], row["status_label"]),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="0.75rem",
            width="100%",
        ),
        rx.text(
            row["symptoms"],
            size="2",
            color="var(--vitta-text-muted)",
            line_height="1.5",
            margin_top="0.65rem",
            overflow_wrap="anywhere",
        ),
        class_name="vitta-data-row",
    )


def reception_preview() -> rx.Component:
    """Read-only operational dashboard inspired by the supplied reception reference."""
    return rx.vstack(
        page_header(
            "Operação",
            "Recepção",
            "Visão consolidada da fila persistida. Agenda e consultas entram quando a capability de agendamento for aplicada.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        rx.cond(
            AdminPreviewState.is_loading,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Carregando operação…", color="var(--vitta-text-muted)", size="2"),
                    spacing="2",
                    align="center",
                ),
                min_height="15rem",
                role="status",
                aria_live="polite",
            ),
            rx.vstack(
                rx.grid(
                    metric_card("Aguardando", AdminPreviewState.waiting_count, "fila ativa"),
                    metric_card("Em atendimento", AdminPreviewState.attending_count, "atendimentos operacionais"),
                    metric_card("Finalizados", AdminPreviewState.finalized_count, "histórico persistido"),
                    metric_card("Retirados", AdminPreviewState.withdrawn_count, "histórico preservado"),
                    columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                    gap="0.75rem",
                    width="100%",
                ),
                rx.grid(
                    section_panel(
                        rx.hstack(
                            rx.box(
                                rx.heading("Fila e operação", size="5"),
                                rx.text(
                                    "Entradas reais registradas no banco, em ordem mais recente primeiro.",
                                    size="2",
                                    color="var(--vitta-text-muted)",
                                    margin_top="0.25rem",
                                ),
                            ),
                            rx.badge(
                                "Somente leitura",
                                color_scheme="gray",
                                variant="soft",
                            ),
                            justify="between",
                            align="start",
                            width="100%",
                            gap="1rem",
                        ),
                        rx.cond(
                            AdminPreviewState.queue_rows.length() > 0,
                            rx.vstack(
                                rx.foreach(AdminPreviewState.queue_rows, _queue_row),
                                spacing="2",
                                align="stretch",
                                width="100%",
                                margin_top="1rem",
                            ),
                            empty_state(
                                "users",
                                "Fila vazia",
                                "Nenhuma entrada de fila foi persistida ainda. Cadastros e mutações continuam exclusivos da Recepção.",
                            ),
                        ),
                    ),
                    section_panel(
                        rx.heading("Agenda", size="5"),
                        rx.text(
                            "A referência visual já está incorporada ao fluxo, mas nenhum horário será inventado antes da implementação da agenda.",
                            size="2",
                            color="var(--vitta-text-muted)",
                            line_height="1.55",
                            margin_top="0.25rem",
                        ),
                        empty_state(
                            "calendar",
                            "Agenda ainda sem dados",
                            "A change add-appointment-scheduling está planejada. Quando for aplicada, esta área passa a refletir slots e Consultas reais.",
                        ),
                    ),
                    columns=rx.breakpoints(initial="1", xl="2"),
                    gap="1rem",
                    width="100%",
                ),
                spacing="4",
                align="stretch",
                width="100%",
            ),
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def _professional_chip(row) -> rx.Component:
    return rx.hstack(
        rx.box(
            width="0.45rem",
            height="0.45rem",
            border_radius="999px",
            background=rx.cond(
                row["is_active"],
                "var(--vitta-success)",
                "var(--vitta-text-subtle)",
            ),
            aria_hidden="true",
        ),
        rx.text(row["name"], size="2", font_weight="650"),
        rx.text(
            row["registration_identifier"],
            font_size="0.72rem",
            color="var(--vitta-text-subtle)",
        ),
        spacing="2",
        align="center",
        class_name="vitta-professional-chip",
    )


def _week_cell(day: str) -> rx.Component:
    return rx.box(
        rx.text(day, font_size="0.72rem", font_weight="800", color="var(--vitta-text-muted)"),
        rx.center(
            rx.text(
                "Sem slots",
                font_size="0.72rem",
                color="var(--vitta-text-subtle)",
            ),
            min_height="7rem",
        ),
        class_name="vitta-week-cell",
    )


def agenda_preview() -> rx.Component:
    """Structural agenda preview with no fabricated appointments."""
    return rx.vstack(
        page_header(
            "Planejamento",
            "Agenda clínica",
            "Estrutura semanal preparada para receber disponibilidade e Consultas reais, sem compromissos de demonstração.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        section_panel(
            rx.flex(
                rx.box(
                    rx.heading("Profissionais", size="5"),
                    rx.text(
                        "Diretório real disponível para a futura agenda.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.25rem",
                    ),
                ),
                rx.hstack(
                    rx.text(
                        AdminPreviewState.professionals.length(),
                        font_weight="800",
                        class_name="vitta-tabular",
                    ),
                    rx.text("profissionais", font_size="0.74rem"),
                    spacing="1",
                    align="center",
                    color="var(--vitta-primary)",
                    padding="0.35rem 0.55rem",
                    border_radius="999px",
                    background="var(--vitta-primary-soft)",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="0.75rem",
                width="100%",
            ),
            rx.cond(
                AdminPreviewState.professionals.length() > 0,
                rx.flex(
                    rx.foreach(AdminPreviewState.professionals, _professional_chip),
                    gap="0.5rem",
                    flex_wrap="wrap",
                    margin_top="1rem",
                    width="100%",
                ),
                rx.text(
                    "Nenhum profissional cadastrado ainda.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="1rem",
                ),
            ),
        ),
        section_panel(
            rx.hstack(
                rx.box(
                    rx.heading("Grade semanal", size="5"),
                    rx.text(
                        "A grade é apenas estrutural até que slots sejam persistidos.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.25rem",
                    ),
                ),
                rx.badge("Sem dados simulados", color_scheme="gray", variant="soft"),
                justify="between",
                align="start",
                width="100%",
                gap="1rem",
            ),
            rx.box(
                _week_cell("Segunda"),
                _week_cell("Terça"),
                _week_cell("Quarta"),
                _week_cell("Quinta"),
                _week_cell("Sexta"),
                class_name="vitta-week-grid",
                margin_top="1rem",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("info", size=17),
                    rx.text(
                        "Disponibilidade, prevenção de conflito, agendamento, reagendamento e cancelamento estão especificados na change add-appointment-scheduling.",
                        size="2",
                        line_height="1.55",
                    ),
                    spacing="2",
                    align="start",
                ),
                class_name="vitta-info-strip",
                margin_top="1rem",
            ),
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def _patient_list_row(row) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.box(
                rx.icon("user", size=16),
                class_name="vitta-patient-avatar",
            ),
            rx.box(
                rx.text(
                    row["name"],
                    font_weight="700",
                    size="2",
                    text_align="left",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.text(
                    row["cpf_masked"],
                    font_size="0.72rem",
                    color="var(--vitta-text-subtle)",
                    class_name="vitta-tabular",
                    text_align="left",
                ),
                min_width="0",
                flex="1",
            ),
            rx.icon("chevron_right", size=16, color="var(--vitta-text-subtle)"),
            spacing="3",
            align="center",
            width="100%",
        ),
        type="button",
        variant="ghost",
        color_scheme="gray",
        width="100%",
        class_name="vitta-patient-list-button",
        on_click=AdminPreviewState.select_patient(
            row["id"],
            row["name"],
            row["cpf_masked"],
        ),
    )


def _history_row(row) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(class_name="vitta-timeline-dot", aria_hidden="true"),
            rx.box(
                rx.hstack(
                    rx.text(row["entered_at"], font_size="0.72rem", color="var(--vitta-text-subtle)"),
                    _status_badge(row["status"], row["status_label"]),
                    _priority_badge(row["priority"], row["priority_label"]),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                rx.text(
                    row["symptoms"],
                    size="2",
                    line_height="1.55",
                    color="var(--vitta-text-muted)",
                    margin_top="0.45rem",
                ),
                min_width="0",
                flex="1",
            ),
            spacing="3",
            align="start",
        ),
        class_name="vitta-timeline-row",
    )


def patients_preview() -> rx.Component:
    """Patient list + profile flow based only on the existing patient/queue domain."""
    return rx.vstack(
        page_header(
            "Cadastros",
            "Pacientes",
            "Consulte pacientes persistidos e o histórico operacional já existente. Dados clínicos futuros permanecem indisponíveis.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        rx.grid(
            section_panel(
                rx.heading("Pacientes", size="5"),
                rx.box(
                    rx.icon(
                        "search",
                        size=17,
                        position="absolute",
                        left="0.8rem",
                        top="50%",
                        transform="translateY(-50%)",
                        color="var(--vitta-text-subtle)",
                        pointer_events="none",
                    ),
                    rx.el.input(
                        type="text",
                        value=AdminPreviewState.patient_query,
                        on_change=AdminPreviewState.update_patient_query,
                        placeholder="Buscar por nome ou CPF mascarado",
                        class_name="vitta-input vitta-search-input",
                        aria_label="Buscar pacientes",
                    ),
                    rx.cond(
                        AdminPreviewState.patient_query != "",
                        rx.button(
                            rx.icon("x", size=16),
                            type="button",
                            variant="ghost",
                            size="1",
                            class_name="vitta-search-clear",
                            aria_label="Limpar busca",
                            on_click=AdminPreviewState.clear_patient_query,
                        ),
                        rx.fragment(),
                    ),
                    position="relative",
                    margin_top="0.9rem",
                ),
                rx.cond(
                    AdminPreviewState.filtered_patients.length() > 0,
                    rx.vstack(
                        rx.foreach(AdminPreviewState.filtered_patients, _patient_list_row),
                        spacing="1",
                        align="stretch",
                        width="100%",
                        margin_top="0.8rem",
                        class_name="vitta-patient-list",
                    ),
                    empty_state(
                        "user",
                        "Nenhum paciente encontrado",
                        "A lista usa somente pacientes persistidos. Ajuste a busca ou cadastre pacientes pela Recepção.",
                    ),
                ),
                class_name="vitta-patient-browser",
            ),
            section_panel(
                rx.cond(
                    AdminPreviewState.selected_patient_id > 0,
                    rx.vstack(
                        rx.flex(
                            rx.hstack(
                                rx.box(
                                    rx.icon("user", size=22),
                                    class_name="vitta-profile-avatar",
                                ),
                                rx.box(
                                    rx.heading(AdminPreviewState.selected_patient_name, size="6"),
                                    rx.text(
                                        AdminPreviewState.selected_patient_cpf,
                                        size="2",
                                        color="var(--vitta-text-subtle)",
                                        class_name="vitta-tabular",
                                        margin_top="0.15rem",
                                    ),
                                ),
                                spacing="3",
                                align="center",
                            ),
                            rx.badge("Paciente", color_scheme="teal", variant="soft"),
                            justify="between",
                            align="center",
                            width="100%",
                            gap="1rem",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Histórico operacional", font_weight="750", size="2"),
                                rx.text(
                                    "Fila registrada",
                                    font_size="0.72rem",
                                    color="var(--vitta-text-subtle)",
                                ),
                                justify="between",
                                align="center",
                                width="100%",
                            ),
                            rx.cond(
                                AdminPreviewState.selected_patient_history.length() > 0,
                                rx.vstack(
                                    rx.foreach(AdminPreviewState.selected_patient_history, _history_row),
                                    spacing="0",
                                    align="stretch",
                                    width="100%",
                                    margin_top="0.8rem",
                                ),
                                empty_state(
                                    "activity",
                                    "Sem passagens registradas",
                                    "Este paciente ainda não possui entradas persistidas na fila.",
                                ),
                            ),
                            margin_top="1rem",
                        ),
                        rx.box(
                            rx.hstack(
                                rx.icon("file_text", size=18),
                                rx.box(
                                    rx.text("Prontuário clínico", font_weight="750", size="2"),
                                    rx.text(
                                        "Diagnósticos, prescrições e exames serão exibidos aqui somente após suas capabilities serem implementadas.",
                                        size="2",
                                        color="var(--vitta-text-muted)",
                                        line_height="1.5",
                                        margin_top="0.2rem",
                                    ),
                                ),
                                spacing="3",
                                align="start",
                            ),
                            class_name="vitta-future-module",
                        ),
                        spacing="4",
                        align="stretch",
                        width="100%",
                    ),
                    empty_state(
                        "user",
                        "Selecione um paciente",
                        "Escolha um paciente da lista para consultar os dados existentes e seu histórico operacional.",
                    ),
                )
            ),
            columns=rx.breakpoints(initial="1", lg="minmax(18rem, 0.72fr) minmax(0, 1.8fr)"),
            gap="1rem",
            width="100%",
            align_items="start",
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def _clinical_row(row) -> rx.Component:
    return section_panel(
        rx.flex(
            rx.hstack(
                rx.box(
                    rx.icon("user", size=18),
                    class_name="vitta-patient-avatar",
                ),
                rx.box(
                    rx.text(row["patient_name"], font_weight="800", size="3"),
                    rx.text(
                        row["entered_at"],
                        font_size="0.72rem",
                        color="var(--vitta-text-subtle)",
                        class_name="vitta-tabular",
                    ),
                ),
                spacing="3",
                align="center",
            ),
            _priority_badge(row["priority"], row["priority_label"]),
            justify="between",
            align="center",
            width="100%",
            gap="1rem",
        ),
        rx.box(
            rx.text("Relato recebido", font_size="0.72rem", font_weight="800", color="var(--vitta-text-subtle)"),
            rx.text(row["symptoms"], size="2", line_height="1.55", margin_top="0.3rem"),
            margin_top="1rem",
        ),
        rx.box(
            rx.grid(
                rx.box(
                    rx.text("Queixa principal", font_weight="750", size="2"),
                    rx.text("Aguardando capability clínica", size="1", color="var(--vitta-text-subtle)", margin_top="0.25rem"),
                    class_name="vitta-clinical-placeholder",
                ),
                rx.box(
                    rx.text("Anamnese", font_weight="750", size="2"),
                    rx.text("Aguardando capability clínica", size="1", color="var(--vitta-text-subtle)", margin_top="0.25rem"),
                    class_name="vitta-clinical-placeholder",
                ),
                rx.box(
                    rx.text("Diagnóstico e conduta", font_weight="750", size="2"),
                    rx.text("Aguardando capability clínica", size="1", color="var(--vitta-text-subtle)", margin_top="0.25rem"),
                    class_name="vitta-clinical-placeholder",
                ),
                columns=rx.breakpoints(initial="1", md="3"),
                gap="0.65rem",
                width="100%",
            ),
            margin_top="1rem",
        ),
    )


def clinical_preview() -> rx.Component:
    """Clinical-workspace structure using only currently active queue data."""
    return rx.vstack(
        page_header(
            "Médico",
            "Atendimento clínico",
            "Visualize atendimentos operacionais ativos sem antecipar prontuário, diagnóstico ou prescrição.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        rx.cond(
            AdminPreviewState.active_clinical_rows.length() > 0,
            rx.vstack(
                rx.foreach(AdminPreviewState.active_clinical_rows, _clinical_row),
                spacing="3",
                align="stretch",
                width="100%",
            ),
            section_panel(
                empty_state(
                    "stethoscope",
                    "Nenhum atendimento ativo",
                    "Quando um Médico chamar um paciente da fila, o contexto operacional real aparecerá aqui. Campos clínicos continuarão bloqueados até a capability correspondente.",
                )
            ),
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )


def finance_preview() -> rx.Component:
    """Honest preview for the future Finance capability."""
    return rx.vstack(
        page_header(
            "Operação financeira",
            "Financeiro",
            "A navegação e o shell estão prontos; valores, pagamentos e integração Asaas ainda não foram implementados.",
        ),
        _preview_notice(),
        section_panel(
            empty_state(
                "wallet",
                "Financeiro aguardando implementação",
                "Nenhum valor ou indicador financeiro de demonstração é exibido. A futura capability usará apenas pagamentos reais persistidos e o Asaas sandbox.",
            )
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )
