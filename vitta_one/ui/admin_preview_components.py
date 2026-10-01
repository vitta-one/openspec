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


def _preview_slot_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["starts_at"], font_weight="750", size="2", class_name="vitta-tabular"),
                rx.text(row["professional_name"], size="1", color="var(--vitta-text-muted)", margin_top="0.15rem"),
            ),
            rx.badge(
                row["status_label"],
                color_scheme=rx.cond(
                    row["status"] == "AVAILABLE",
                    "green",
                    rx.cond(row["status"] == "BOOKED", "blue", "gray"),
                ),
                variant="soft",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="0.6rem",
            width="100%",
        ),
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _preview_consultation_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["scheduled_at"], font_weight="750", size="2", class_name="vitta-tabular"),
                rx.text(row["patient_name"], size="2", margin_top="0.2rem"),
                rx.text(row["professional_name"], size="1", color="var(--vitta-text-muted)", margin_top="0.1rem"),
            ),
            rx.badge(
                row["status_label"],
                color_scheme=rx.cond(row["status"] == "CANCELADA", "red", "blue"),
                variant="soft",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="0.6rem",
            width="100%",
        ),
        class_name="vitta-schedule-row",
        role="listitem",
    )


def agenda_preview() -> rx.Component:
    """Read-only local QA projection of persisted scheduling data."""
    return rx.vstack(
        page_header(
            "Agenda",
            "Agenda clínica",
            "Confira slots e Consultas persistidos sem conceder à sessão Administrador as mutações exclusivas da Recepção.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        rx.grid(
            section_panel(
                rx.heading("Disponibilidade", size="5"),
                rx.text(
                    "Slots reais cadastrados pela Administração.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.25rem",
                ),
                rx.cond(
                    AdminPreviewState.agenda_slots.length() > 0,
                    rx.vstack(
                        rx.foreach(AdminPreviewState.agenda_slots, _preview_slot_row),
                        spacing="2",
                        align="stretch",
                        width="100%",
                        role="list",
                        margin_top="1rem",
                    ),
                    empty_state(
                        "calendar",
                        "Nenhum horário persistido",
                        "Cadastre disponibilidade em Administração para vê-la neste preview.",
                    ),
                ),
            ),
            section_panel(
                rx.heading("Consultas", size="5"),
                rx.text(
                    "Agendamentos e cancelamentos reais do período persistido.",
                    size="2",
                    color="var(--vitta-text-muted)",
                    margin_top="0.25rem",
                ),
                rx.cond(
                    AdminPreviewState.agenda_consultations.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            AdminPreviewState.agenda_consultations,
                            _preview_consultation_row,
                        ),
                        spacing="2",
                        align="stretch",
                        width="100%",
                        role="list",
                        margin_top="1rem",
                    ),
                    empty_state(
                        "calendar",
                        "Nenhuma consulta persistida",
                        "Quando a Recepção fizer um agendamento, ele aparecerá aqui em modo somente leitura.",
                    ),
                ),
            ),
            columns=rx.breakpoints(initial="1", xl="1fr 1fr"),
            gap="1rem",
            width="100%",
            align_items="start",
        ),
        spacing="5",
        align="stretch",
        width="100%",
    )

def _patient_list_row(row) -> rx.Component:
    is_selected = AdminPreviewState.selected_patient_id == row["id"]
    return rx.box(
        rx.hstack(
            rx.checkbox(
                checked=is_selected,
                on_change=lambda checked: AdminPreviewState.toggle_patient_selection(
                    row["id"],
                    row["name"],
                    row["cpf_masked"],
                    checked,
                ),
                color_scheme="teal",
                high_contrast=True,
                size="2",
                aria_label=row["name"],
            ),
            rx.box(
                rx.icon("user", size=16),
                class_name="vitta-patient-avatar",
            ),
            rx.box(
                rx.text(
                    row["name"],
                    font_weight="720",
                    size="2",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    white_space="nowrap",
                ),
                rx.text(
                    row["cpf_masked"],
                    font_size="0.74rem",
                    color="var(--vitta-text-subtle)",
                    class_name="vitta-tabular",
                    margin_top="0.12rem",
                ),
                min_width="0",
                flex="1",
            ),
            rx.cond(
                is_selected,
                rx.badge(
                    "Selecionado",
                    color_scheme="teal",
                    variant="soft",
                    high_contrast=True,
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        class_name="vitta-patient-row",
        border_color=rx.cond(
            is_selected,
            "var(--vitta-primary)",
            "var(--vitta-border)",
        ),
        background=rx.cond(
            is_selected,
            "var(--vitta-primary-soft)",
            "var(--vitta-surface)",
        ),
        role="listitem",
        aria_selected=is_selected,
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


def _patient_search_bar() -> rx.Component:
    return section_panel(
        rx.flex(
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
                    type="search",
                    value=AdminPreviewState.patient_query,
                    on_change=AdminPreviewState.update_patient_query,
                    placeholder="Buscar paciente por nome ou CPF mascarado",
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
                flex="1 1 28rem",
                min_width="0",
            ),
            rx.hstack(
                rx.icon("users", size=16),
                rx.text(
                    AdminPreviewState.patient_range_label,
                    size="2",
                    font_weight="650",
                    class_name="vitta-tabular",
                ),
                spacing="2",
                align="center",
                color="var(--vitta-text-muted)",
                flex="0 0 auto",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            align=rx.breakpoints(initial="stretch", sm="center"),
            gap="0.75rem",
            width="100%",
        ),
    )


def _patient_pagination() -> rx.Component:
    return rx.flex(
        rx.text(
            AdminPreviewState.patient_range_label,
            size="1",
            color="var(--vitta-text-subtle)",
            class_name="vitta-tabular",
        ),
        rx.hstack(
            rx.button(
                rx.icon("chevron_left", size=16),
                type="button",
                variant="outline",
                color_scheme="gray",
                size="2",
                aria_label="Página anterior de pacientes",
                on_click=AdminPreviewState.previous_patient_page,
                disabled=~AdminPreviewState.can_previous_patient_page,
            ),
            rx.text(
                "Página ",
                AdminPreviewState.patient_page,
                " de ",
                AdminPreviewState.patient_total_pages,
                size="2",
                font_weight="650",
                class_name="vitta-tabular",
                min_width="7rem",
                text_align="center",
            ),
            rx.button(
                rx.icon("chevron_right", size=16),
                type="button",
                variant="outline",
                color_scheme="gray",
                size="2",
                aria_label="Próxima página de pacientes",
                on_click=AdminPreviewState.next_patient_page,
                disabled=~AdminPreviewState.can_next_patient_page,
            ),
            spacing="2",
            align="center",
        ),
        direction=rx.breakpoints(initial="column", sm="row"),
        justify="between",
        align=rx.breakpoints(initial="stretch", sm="center"),
        gap="0.75rem",
        width="100%",
        padding_top="0.9rem",
        border_top="1px solid var(--vitta-border)",
    )


def _patient_selection_bar() -> rx.Component:
    return rx.cond(
        AdminPreviewState.selected_patient_id > 0,
        rx.box(
            rx.flex(
                rx.hstack(
                    rx.box(
                        rx.icon("user", size=18),
                        class_name="vitta-patient-avatar",
                    ),
                    rx.box(
                        rx.text(
                            AdminPreviewState.selected_patient_name,
                            font_weight="750",
                            size="2",
                        ),
                        rx.text(
                            AdminPreviewState.selected_patient_cpf,
                            font_size="0.72rem",
                            color="var(--vitta-text-subtle)",
                            class_name="vitta-tabular",
                            margin_top="0.12rem",
                        ),
                    ),
                    spacing="3",
                    align="center",
                    min_width="0",
                ),
                rx.hstack(
                    rx.link(
                        rx.hstack(
                            rx.icon("history", size=16),
                            rx.text("Ver histórico"),
                            spacing="2",
                            align="center",
                        ),
                        href="#patient-history",
                        class_name="vitta-context-link",
                    ),
                    rx.button(
                        "Limpar seleção",
                        type="button",
                        variant="ghost",
                        color_scheme="gray",
                        on_click=AdminPreviewState.clear_patient_selection,
                    ),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                align=rx.breakpoints(initial="stretch", sm="center"),
                justify="between",
                gap="0.75rem",
                width="100%",
            ),
            class_name="vitta-selection-bar",
            role="region",
            aria_label="Ações do paciente selecionado",
        ),
        rx.box(
            rx.hstack(
                rx.icon("info", size=17),
                rx.text(
                    "Selecione um paciente pelo checkbox para consultar o histórico operacional e as ações disponíveis neste preview.",
                    size="2",
                    line_height="1.5",
                ),
                spacing="2",
                align="start",
            ),
            class_name="vitta-info-strip",
        ),
    )


def patients_preview() -> rx.Component:
    """Paginated read-only patient browser based only on persisted patient/queue data."""
    return rx.vstack(
        page_header(
            "Cadastros",
            "Pacientes",
            "Pesquise pacientes persistidos, selecione um registro e consulte o histórico operacional já existente.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        _patient_search_bar(),
        _patient_selection_bar(),
        section_panel(
            rx.flex(
                rx.box(
                    rx.heading("Lista de pacientes", size="5"),
                    rx.text(
                        "A seleção é individual e somente leitura neste modo local de QA.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        margin_top="0.25rem",
                    ),
                ),
                rx.badge(
                    "1 paciente por vez",
                    color_scheme="gray",
                    variant="soft",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                justify="between",
                align=rx.breakpoints(initial="stretch", sm="start"),
                gap="0.75rem",
                width="100%",
            ),
            rx.cond(
                AdminPreviewState.filtered_patients.length() > 0,
                rx.vstack(
                    rx.vstack(
                        rx.foreach(
                            AdminPreviewState.paginated_patients,
                            _patient_list_row,
                        ),
                        spacing="2",
                        align="stretch",
                        width="100%",
                        role="list",
                        margin_top="1rem",
                    ),
                    _patient_pagination(),
                    spacing="3",
                    align="stretch",
                    width="100%",
                ),
                empty_state(
                    "search",
                    "Nenhum paciente encontrado",
                    "Ajuste a busca. Esta lista usa somente pacientes persistidos e não cria dados de demonstração.",
                ),
            ),
        ),
        rx.cond(
            AdminPreviewState.selected_patient_id > 0,
            section_panel(
                rx.vstack(
                    rx.flex(
                        rx.hstack(
                            rx.box(
                                rx.icon("user", size=22),
                                class_name="vitta-profile-avatar",
                            ),
                            rx.box(
                                rx.heading(
                                    AdminPreviewState.selected_patient_name,
                                    size="6",
                                ),
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
                            rx.text(
                                "Histórico operacional",
                                font_weight="750",
                                size="2",
                            ),
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
                                rx.foreach(
                                    AdminPreviewState.selected_patient_history,
                                    _history_row,
                                ),
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
                    ),
                    rx.box(
                        rx.hstack(
                            rx.icon("file_text", size=18),
                            rx.box(
                                rx.text(
                                    "Prontuário clínico",
                                    font_weight="750",
                                    size="2",
                                ),
                                rx.text(
                                    "Diagnósticos, prescrições e exames serão exibidos somente após suas capabilities serem implementadas.",
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
                id="patient-history",
            ),
            rx.fragment(),
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
