"""Premium read-only screens for the explicitly enabled local Administrator QA mode."""

import reflex as rx

from vitta_one.admin_preview.state import AdminPreviewState
from vitta_one.ui.components import (
    empty_state,
    error_banner,
    breadcrumb,
    field_label,
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


def _preview_lifecycle_meta(row) -> rx.Component:
    return rx.vstack(
        rx.cond(
            row["confirmed_at"] != "",
            rx.text(
                "Chegada confirmada: ",
                row["confirmed_at"],
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-tabular",
            ),
            rx.fragment(),
        ),
        rx.cond(
            row["started_at"] != "",
            rx.text(
                "Atendimento iniciado: ",
                row["started_at"],
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-tabular",
            ),
            rx.fragment(),
        ),
        rx.cond(
            row["completed_at"] != "",
            rx.text(
                "Concluída: ",
                row["completed_at"],
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-tabular",
            ),
            rx.fragment(),
        ),
        rx.cond(
            row["cancelled_at"] != "",
            rx.text(
                "Cancelada: ",
                row["cancelled_at"],
                size="1",
                color="var(--vitta-text-subtle)",
                class_name="vitta-tabular",
            ),
            rx.fragment(),
        ),
        spacing="1",
        align="start",
        margin_top="0.4rem",
    )


def _preview_consultation_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(
                    row["scheduled_at"],
                    font_weight="750",
                    size="2",
                    class_name="vitta-tabular",
                ),
                rx.text(row["patient_name"], size="2", margin_top="0.2rem"),
                rx.text(
                    row["professional_name"],
                    size="1",
                    color="var(--vitta-text-muted)",
                    margin_top="0.1rem",
                ),
                _preview_lifecycle_meta(row),
            ),
            rx.badge(
                row["status_label"],
                color_scheme=rx.match(
                    row["status"],
                    ("CANCELADA", "red"),
                    ("CONCLUIDA", "green"),
                    ("EM_ANDAMENTO", "amber"),
                    ("CONFIRMADA", "teal"),
                    "blue",
                ),
                variant="soft",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="start"),
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
    """Semantic, compact administrative table row with explicit navigation."""
    return rx.table.row(
        rx.table.row_header_cell(
            rx.hstack(
                rx.box(rx.icon("user", size=17), class_name="vitta-patient-avatar"),
                rx.box(
                    rx.text(
                        row["name"], font_weight="700", size="2",
                        overflow_wrap="anywhere",
                    ),
                    rx.text(
                        row["cpf_masked"], size="1",
                        class_name="vitta-tabular",
                        color="var(--vitta-text-muted)",
                        display=rx.breakpoints(initial="block", sm="none"),
                    ),
                    min_width="0",
                ),
                align="center",
                spacing="2",
                min_width="0",
            ),
        ),
        rx.table.cell(
            rx.text(row["cpf_masked"], class_name="vitta-tabular", size="2"),
            display=rx.breakpoints(initial="none", sm="table-cell"),
        ),
        rx.table.cell(
            rx.link(
                "Ver detalhes",
                href="/admin/pacientes/" + row["id"].to(str),
                class_name="vitta-context-link",
                aria_label="Ver detalhes de " + row["name"],
                white_space="nowrap",
            ),
            justify="end",
        ),
        align="center",
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
                field_label("Pesquisar pacientes", "admin-patient-search"),
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
                        id="admin-patient-search",
                        type="search",
                        value=AdminPreviewState.patient_query,
                        on_change=AdminPreviewState.update_patient_query,
                        placeholder="Nome ou CPF mascarado",
                        class_name="vitta-input vitta-search-input",
                        aria_label="Pesquisar pacientes",
                        auto_complete="off",
                    ),
                    rx.cond(
                        AdminPreviewState.patient_query != "",
                        rx.button(
                            rx.icon("x", size=16),
                            type="button",
                            variant="ghost",
                            size="1",
                            class_name="vitta-search-clear",
                            aria_label="Limpar busca de pacientes",
                            on_click=AdminPreviewState.clear_patient_query,
                        ),
                        rx.fragment(),
                    ),
                    position="relative",
                    width="100%",
                    margin_top="0.3rem",
                ),
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
            align=rx.breakpoints(initial="stretch", sm="end"),
            gap="0.75rem",
            width="100%",
        ),
    )

def _patient_pagination() -> rx.Component:
    return rx.flex(
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
                text_align="center",
                min_width="6rem",
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
        justify="end",
        width="100%",
        padding_top="0.85rem",
        border_top="1px solid var(--vitta-border)",
    )


# Patient selection was removed: the list links to a dedicated, guarded detail route.

def _readonly_clinical_value(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(
            label,
            size="1",
            font_weight="750",
            color="var(--vitta-text-muted)",
        ),
        rx.cond(
            value != "",
            rx.text(
                value,
                size="2",
                line_height="1.6",
                white_space="pre-wrap",
                overflow_wrap="anywhere",
                margin_top="0.25rem",
            ),
            rx.text(
                "Não registrado",
                size="2",
                color="var(--vitta-text-subtle)",
                margin_top="0.25rem",
            ),
        ),
        width="100%",
    )


def _admin_prescription_item(item) -> rx.Component:
    return rx.box(
        rx.text(
            item["medication_or_item"],
            font_weight="800",
            size="2",
            overflow_wrap="anywhere",
        ),
        rx.text(
            item["instructions"],
            size="2",
            line_height="1.55",
            white_space="pre-wrap",
            overflow_wrap="anywhere",
            margin_top="0.25rem",
        ),
        rx.cond(
            item["notes"] != "",
            rx.text(
                item["notes"],
                size="1",
                color="var(--vitta-text-muted)",
                line_height="1.5",
                white_space="pre-wrap",
                overflow_wrap="anywhere",
                margin_top="0.3rem",
            ),
            rx.fragment(),
        ),
        class_name="vitta-prescription-item",
        role="listitem",
    )


def _admin_prescription_document(row) -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            rx.flex(
                rx.box(
                    rx.text("Prescrição", font_weight="800", size="2"),
                    rx.text(
                        row["created_at"],
                        size="1",
                        color="var(--vitta-text-subtle)",
                        class_name="vitta-tabular",
                        margin_top="0.1rem",
                    ),
                ),
                rx.badge(
                    row["item_count"],
                    " itens",
                    color_scheme="teal",
                    variant="soft",
                ),
                justify="between",
                align="center",
                gap="0.75rem",
                width="100%",
            ),
            class_name="vitta-disclosure-summary",
        ),
        rx.vstack(
            rx.vstack(
                rx.foreach(row["items"], _admin_prescription_item),
                spacing="2",
                align="stretch",
                width="100%",
                role="list",
            ),
            rx.cond(
                row["general_notes"] != "",
                _readonly_clinical_value(
                    "Observações gerais",
                    row["general_notes"],
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="stretch",
            width="100%",
            padding_top="0.7rem",
        ),
        class_name="vitta-prescription-history-disclosure",
    )


def _admin_prescriptions_block(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text("Prescrições", font_weight="750", size="2"),
            rx.cond(
                row["prescription_count"] > 0,
                rx.badge(
                    row["prescription_count"],
                    color_scheme="teal",
                    variant="soft",
                ),
                rx.fragment(),
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.cond(
            row["prescription_count"] > 0,
            rx.vstack(
                rx.foreach(row["prescriptions"], _admin_prescription_document),
                spacing="2",
                align="stretch",
                width="100%",
                margin_top="0.65rem",
            ),
            rx.text(
                "Sem prescrições neste atendimento.",
                size="2",
                color="var(--vitta-text-subtle)",
                margin_top="0.5rem",
            ),
        ),
        width="100%",
        padding_top="0.85rem",
        border_top="1px solid var(--vitta-border)",
    )


def _admin_clinical_history_card(row) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.flex(
                rx.box(
                    rx.text(row["completed_at"], size="2", font_weight="800"),
                    rx.text(
                        row["professional_name"],
                        size="1",
                        color="var(--vitta-text-muted)",
                        margin_top="0.15rem",
                    ),
                ),
                rx.badge(
                    "Concluído",
                    color_scheme="green",
                    variant="soft",
                    high_contrast=True,
                ),
                justify="between",
                align="start",
                gap="0.75rem",
                width="100%",
            ),
            rx.grid(
                _readonly_clinical_value("Queixa principal", row["chief_complaint"]),
                _readonly_clinical_value("Anamnese", row["anamnesis"]),
                _readonly_clinical_value("Diagnóstico", row["diagnosis"]),
                _readonly_clinical_value(
                    "Conduta e observações",
                    row["conduct_notes"],
                ),
                columns=rx.breakpoints(initial="1", lg="2"),
                gap="0.9rem",
                width="100%",
            ),
            _admin_prescriptions_block(row),
            spacing="3",
            align="stretch",
            width="100%",
        ),
        class_name="vitta-clinical-history-card",
        role="listitem",
    )


def _admin_clinical_history_panel() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading("Histórico clínico", size="4"),
                rx.text(
                    "Projeção local de QA · somente atendimentos concluídos",
                    size="1",
                    color="var(--vitta-text-subtle)",
                    margin_top="0.15rem",
                ),
            ),
            rx.cond(
                AdminPreviewState.clinical_history_total_count > 0,
                rx.badge(
                    AdminPreviewState.clinical_history_total_count,
                    " registros",
                    color_scheme="gray",
                    variant="soft",
                ),
                rx.fragment(),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="stretch", sm="start"),
            gap="0.5rem",
            width="100%",
        ),
        rx.cond(
            AdminPreviewState.is_loading_clinical_history,
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text(
                        "Carregando histórico clínico…",
                        size="2",
                        color="var(--vitta-text-muted)",
                    ),
                    spacing="2",
                    align="center",
                ),
                min_height="7rem",
                width="100%",
                role="status",
                aria_live="polite",
            ),
            rx.cond(
                AdminPreviewState.selected_clinical_history.length() > 0,
                rx.vstack(
                    rx.vstack(
                        rx.foreach(
                            AdminPreviewState.selected_clinical_history,
                            _admin_clinical_history_card,
                        ),
                        spacing="3",
                        align="stretch",
                        width="100%",
                        role="list",
                    ),
                    rx.flex(
                        rx.text(
                            "Página ",
                            AdminPreviewState.clinical_history_page,
                            " de ",
                            AdminPreviewState.clinical_history_total_pages,
                            size="1",
                            color="var(--vitta-text-muted)",
                        ),
                        rx.hstack(
                            rx.button(
                                "Anterior",
                                type="button",
                                variant="outline",
                                color_scheme="gray",
                                size="2",
                                on_click=AdminPreviewState.previous_clinical_history_page,
                                disabled=~AdminPreviewState.can_previous_clinical_history_page
                                | AdminPreviewState.is_loading_clinical_history,
                            ),
                            rx.button(
                                "Próxima",
                                type="button",
                                variant="outline",
                                color_scheme="gray",
                                size="2",
                                on_click=AdminPreviewState.next_clinical_history_page,
                                disabled=~AdminPreviewState.can_next_clinical_history_page
                                | AdminPreviewState.is_loading_clinical_history,
                            ),
                            spacing="2",
                        ),
                        direction=rx.breakpoints(initial="column", sm="row"),
                        justify="between",
                        align=rx.breakpoints(initial="stretch", sm="center"),
                        gap="0.6rem",
                        width="100%",
                    ),
                    spacing="3",
                    align="stretch",
                    width="100%",
                    margin_top="0.8rem",
                ),
                rx.box(
                    rx.text(
                        "Não há registros clínicos concluídos disponíveis para esta visualização.",
                        color="var(--vitta-text-muted)",
                        size="2",
                    ),
                    role="status",
                    padding="1rem 0",
                ),
            ),
        ),
        margin_top="0.9rem",
        width="100%",
    )


def patients_preview() -> rx.Component:
    """Find patients in a read-only table; no history is loaded on this route."""
    return rx.vstack(
        page_header(
            "Administração",
            "Pacientes",
            "Localize um cadastro e abra sua ficha para consultar os históricos autorizados.",
        ),
        _preview_notice(),
        rx.cond(
            AdminPreviewState.error_message != "",
            error_banner(AdminPreviewState.error_message),
            rx.fragment(),
        ),
        _patient_search_bar(),
        section_panel(
            rx.cond(
                AdminPreviewState.is_loading,
                rx.center(
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("Carregando pacientes…", size="2"),
                        spacing="3",
                    ),
                    min_height="8rem",
                    role="status",
                    aria_live="polite",
                ),
                rx.cond(
                    AdminPreviewState.patient_result_count > 0,
                    rx.vstack(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Paciente"),
                                    rx.table.column_header_cell(
                                        "CPF mascarado",
                                        display=rx.breakpoints(initial="none", sm="table-cell"),
                                    ),
                                    rx.table.column_header_cell("Ações", justify="end"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AdminPreviewState.paginated_patients,
                                    _patient_list_row,
                                ),
                            ),
                            width="100%",
                            size="1",
                            variant="surface",
                        ),
                        rx.cond(
                            AdminPreviewState.patient_total_pages > 1,
                            _patient_pagination(),
                            rx.fragment(),
                        ),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    rx.box(
                        rx.text(
                            rx.cond(
                                AdminPreviewState.patient_query != "",
                                "Nenhum paciente encontrado para os filtros selecionados.",
                                "Nenhum paciente cadastrado.",
                            ),
                            size="2",
                            color="var(--vitta-text-muted)",
                        ),
                        padding="1.25rem 0",
                        role="status",
                        aria_live="polite",
                    ),
                ),
            ),
        ),
        spacing="4",
        align="stretch",
        width="100%",
    )


def patient_detail_preview() -> rx.Component:
    """One read-only QA patient dossier with independently authorized histories."""
    return rx.vstack(
        breadcrumb(
            ("Administração", "/admin"),
            ("Pacientes", "/admin/pacientes"),
            ("Ficha do paciente", None),
        ),
        rx.cond(
            AdminPreviewState.detail_status == "ready",
            rx.vstack(
                page_header(
                    "Pacientes",
                    "Ficha do paciente",
                    "Identificação e histórico do cadastro, disponíveis apenas no modo QA.",
                ),
                _preview_notice(),
                rx.cond(
                    AdminPreviewState.error_message != "",
                    error_banner(AdminPreviewState.error_message),
                    rx.fragment(),
                ),
                section_panel(
                    rx.hstack(
                        rx.box(
                            rx.icon("user", size=22),
                            class_name="vitta-profile-avatar",
                        ),
                        rx.box(
                            rx.heading(
                                AdminPreviewState.selected_patient_name,
                                size="6",
                                overflow_wrap="anywhere",
                            ),
                            rx.text(
                                "CPF " + AdminPreviewState.selected_patient_cpf,
                                size="2",
                                color="var(--vitta-text-muted)",
                                class_name="vitta-tabular",
                                margin_top="0.2rem",
                            ),
                            min_width="0",
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                ),
                rx.flex(
                    rx.button(
                        "Histórico operacional",
                        type="button",
                        color_scheme="teal",
                        variant=rx.cond(
                            AdminPreviewState.active_patient_tab == "operacional",
                            "solid",
                            "outline",
                        ),
                        aria_pressed=AdminPreviewState.active_patient_tab == "operacional",
                        on_click=AdminPreviewState.show_operational_history,
                    ),
                    rx.button(
                        "Histórico clínico",
                        type="button",
                        color_scheme="teal",
                        variant=rx.cond(
                            AdminPreviewState.active_patient_tab == "clinico",
                            "solid",
                            "outline",
                        ),
                        aria_pressed=AdminPreviewState.active_patient_tab == "clinico",
                        on_click=AdminPreviewState.show_clinical_history,
                        disabled=AdminPreviewState.is_loading_clinical_history,
                    ),
                    role="group",
                    aria_label="Escolha o histórico do paciente",
                    gap="0.65rem",
                    flex_wrap="wrap",
                ),
                rx.cond(
                    AdminPreviewState.active_patient_tab == "operacional",
                    section_panel(
                        rx.heading("Histórico operacional", size="4"),
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
                            rx.box(
                                rx.text(
                                    "Nenhuma movimentação operacional encontrada para este paciente.",
                                    size="2",
                                    color="var(--vitta-text-muted)",
                                ),
                                role="status",
                                padding_top="0.9rem",
                            ),
                        ),
                    ),
                    section_panel(_admin_clinical_history_panel()),
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            rx.cond(
                AdminPreviewState.detail_status == "loading",
                rx.center(
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("Carregando ficha do paciente…", size="2"),
                        spacing="3",
                    ),
                    min_height="8rem",
                    width="100%",
                    role="status",
                    aria_live="polite",
                ),
                section_panel(
                    rx.vstack(
                        rx.heading(
                            rx.cond(
                                AdminPreviewState.detail_status == "not_found",
                                "Paciente não encontrado.",
                                "Não foi possível consultar a ficha.",
                            ),
                            size="4",
                        ),
                        rx.cond(
                            AdminPreviewState.detail_status == "error",
                            rx.button(
                                "Tentar novamente",
                                on_click=AdminPreviewState.load_patient_detail,
                                variant="outline",
                                color_scheme="teal",
                            ),
                            rx.fragment(),
                        ),
                        rx.link(
                            "Voltar aos pacientes",
                            href="/admin/pacientes",
                            class_name="vitta-context-link",
                        ),
                        spacing="3",
                        align="start",
                    ),
                ),
            ),
        ),
        spacing="4",
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
            rx.text(
                "Relato recebido",
                font_size="0.72rem",
                font_weight="800",
                color="var(--vitta-text-subtle)",
            ),
            rx.text(
                row["symptoms"],
                size="2",
                line_height="1.55",
                white_space="pre-wrap",
                margin_top="0.3rem",
            ),
            margin_top="1rem",
        ),
        rx.cond(
            row["has_clinical_record"],
            rx.vstack(
                rx.grid(
                    _readonly_clinical_value("Queixa principal", row["chief_complaint"]),
                    _readonly_clinical_value("Anamnese", row["anamnesis"]),
                    _readonly_clinical_value("Diagnóstico", row["diagnosis"]),
                    _readonly_clinical_value(
                        "Conduta e observações",
                        row["conduct_notes"],
                    ),
                    columns=rx.breakpoints(initial="1", lg="2"),
                    gap="0.75rem",
                    width="100%",
                ),
                _admin_prescriptions_block(row),
                spacing="3",
                align="stretch",
                width="100%",
                margin_top="1rem",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("info", size=16),
                    rx.text(
                        "Este atendimento não possui ClinicalCareRecord persistido neste fluxo.",
                        size="2",
                        color="var(--vitta-text-muted)",
                    ),
                    spacing="2",
                    align="start",
                ),
                class_name="vitta-info-strip",
                margin_top="1rem",
            ),
        ),
    )

def clinical_preview() -> rx.Component:
    """Clinical-workspace structure using only currently active queue data."""
    return rx.vstack(
        page_header(
            "Médico",
            "Atendimento clínico",
            "Visualize atendimentos ativos, registros clínicos e Prescrições persistidas em modo local somente leitura.",
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
                    "Quando um Médico chamar uma Consulta agendada, o contexto e o registro clínico persistido aparecerão aqui em modo somente leitura.",
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
