"""Premium read-only screens for the explicitly enabled local Administrator QA mode."""

import reflex as rx

from vitta_one.admin_preview.state import AdminPreviewState
from vitta_one.admin_preview.agenda_state import AdminAgendaPreviewState
from vitta_one.ui.calendar_components import month_calendar
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


def _agenda_slot_row(row) -> rx.Component:
    return rx.flex(
        rx.box(
            rx.text(row["time_label"], font_weight="750", size="3", class_name="vitta-tabular"),
            rx.text(row["professional_name"], size="2", color="var(--vitta-text-muted)"),
            min_width="0",
        ),
        rx.badge(
            row["status_label"],
            color_scheme=rx.match(
                row["status"],
                ("AVAILABLE", "green"),
                ("BOOKED", "blue"),
                "gray",
            ),
            high_contrast=True,
            variant="soft",
        ),
        justify="between", align="center", gap="3", width="100%",
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _agenda_consultation_row(row) -> rx.Component:
    return rx.flex(
        rx.box(
            rx.text(row["time_label"], font_weight="750", size="3", class_name="vitta-tabular"),
            rx.text(row["professional_name"], size="2", color="var(--vitta-text-muted)"),
            min_width="0",
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
            high_contrast=True,
        ),
        justify="between", align="center", gap="3", width="100%",
        class_name="vitta-schedule-row",
        role="listitem",
    )


def _agenda_professional_filter() -> rx.Component:
    return rx.box(
        field_label("Profissional", "qa-agenda-professional"),
        rx.select.root(
            rx.select.trigger(
                id="qa-agenda-professional",
                width="100%",
                class_name="vitta-select-trigger",
            ),
            rx.select.content(
                rx.select.item("Todos os profissionais", value="__all__"),
                rx.foreach(
                    AdminAgendaPreviewState.professionals,
                    lambda item: rx.select.item(item["label"], value=item["value"]),
                ),
                position="popper",
            ),
            value=AdminAgendaPreviewState.filter_professional,
            on_change=AdminAgendaPreviewState.filter_by_professional,
            disabled=AdminAgendaPreviewState.is_loading,
            size="3",
        ),
        width=rx.breakpoints(initial="100%", sm="min(24rem, 100%)"),
    )


def _agenda_summary() -> rx.Component:
    return rx.flex(
        rx.badge(
            "Disponíveis: ", AdminAgendaPreviewState.available_count,
            color_scheme="green", variant="soft",
        ),
        rx.badge(
            "Reservados: ", AdminAgendaPreviewState.booked_count,
            color_scheme="blue", variant="soft",
        ),
        rx.badge(
            "Agendadas: ", AdminAgendaPreviewState.scheduled_count,
            color_scheme="teal", variant="soft",
        ),
        rx.badge(
            "Canceladas: ", AdminAgendaPreviewState.cancelled_count,
            color_scheme="red", variant="soft",
        ),
        wrap="wrap", gap="2", width="100%",
        aria_label="Resumo da data selecionada",
    )


def _agenda_pagination(*, page, total, on_previous, on_next) -> rx.Component:
    return rx.cond(
        total > 1,
        rx.flex(
            rx.text("Página ", page, " de ", total, size="2",
                    color="var(--vitta-text-muted)", class_name="vitta-tabular"),
            rx.hstack(
                rx.button(
                    rx.icon("chevron_left", size=16),
                    type="button", size="2", variant="outline",
                    aria_label="Página anterior",
                    disabled=page <= 1, on_click=on_previous,
                ),
                rx.button(
                    rx.icon("chevron_right", size=16),
                    type="button", size="2", variant="outline",
                    aria_label="Próxima página",
                    disabled=page >= total, on_click=on_next,
                ),
                spacing="2",
            ),
            align="center", justify="between", gap="3", width="100%",
            margin_top="0.6rem",
        ),
        rx.fragment(),
    )


def agenda_preview() -> rx.Component:
    """Visualização administrativa de QA, sem ações da Recepção e sem dados clínicos."""
    return rx.vstack(
        page_header(
            "Agenda",
            "Agenda clínica",
            "Consulte a disponibilidade e a situação das consultas por profissional e data.",
        ),
        rx.flex(
            rx.badge(
                "QA · somente leitura",
                color_scheme="gray", variant="soft", high_contrast=True,
            ),
            rx.text(
                "A gestão de horários permanece em Administração / Horários.",
                size="2", color="var(--vitta-text-muted)",
            ),
            gap="3", align="center", wrap="wrap", width="100%",
        ),
        rx.cond(
            AdminAgendaPreviewState.error_message != "",
            section_panel(
                error_banner(AdminAgendaPreviewState.error_message),
                rx.button(
                    "Tentar novamente", type="button", variant="outline",
                    on_click=AdminAgendaPreviewState.reload_agenda,
                ),
            ),
            rx.fragment(),
        ),
        section_panel(
            rx.flex(
                _agenda_professional_filter(),
                rx.hstack(
                    rx.button(
                        rx.icon("x", size=15), "Limpar filtros",
                        type="button", variant="outline", color_scheme="gray",
                        on_click=AdminAgendaPreviewState.clear_filters,
                        disabled=AdminAgendaPreviewState.is_loading,
                    ),
                    rx.button(
                        rx.icon("refresh_cw", size=15), "Atualizar",
                        type="button", variant="outline", color_scheme="teal",
                        on_click=AdminAgendaPreviewState.reload_agenda,
                        disabled=AdminAgendaPreviewState.is_loading,
                    ),
                    spacing="2", align="center", flex_wrap="wrap",
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                align=rx.breakpoints(initial="stretch", md="end"),
                justify="between", gap="3", width="100%",
            ),
            rx.text(
                "Período consultado: ", AdminAgendaPreviewState.month_title,
                size="2", color="var(--vitta-text-muted)",
                margin_top="0.75rem",
            ),
        ),
        rx.cond(
            AdminAgendaPreviewState.error_message == "",
            rx.vstack(
                rx.grid(
                    section_panel(
                        rx.heading("Calendário", size="4"),
                        rx.text(
                            "Selecione um dia para ver os horários persistidos.",
                            size="2", color="var(--vitta-text-muted)",
                            margin_top="0.3rem", margin_bottom="0.9rem",
                        ),
                        month_calendar(
                            month_title=AdminAgendaPreviewState.month_title,
                            days=AdminAgendaPreviewState.calendar_days,
                            is_loading=AdminAgendaPreviewState.is_loading,
                            on_previous=AdminAgendaPreviewState.move_month(-1),
                            on_next=AdminAgendaPreviewState.move_month(1),
                            on_select_day=AdminAgendaPreviewState.select_day,
                            allow_empty=True,
                            show_consultations=True,
                            show_today=True,
                        ),
                    ),
                    section_panel(
                        rx.heading("Disponibilidade do dia", size="4"),
                        rx.text(
                            AdminAgendaPreviewState.selected_day_label,
                            size="2", color="var(--vitta-text-muted)",
                            margin_top="0.3rem", margin_bottom="0.75rem",
                        ),
                        rx.cond(
                            AdminAgendaPreviewState.is_loading,
                            rx.text("Atualizando indicadores…", size="2", color="var(--vitta-text-muted)"),
                            _agenda_summary(),
                        ),
                        rx.cond(
                            AdminAgendaPreviewState.is_loading,
                            rx.center(rx.spinner(size="3"), min_height="8rem"),
                            rx.cond(
                                AdminAgendaPreviewState.day_slots.length() > 0,
                                rx.vstack(
                                    rx.foreach(
                                        AdminAgendaPreviewState.paginated_day_slots,
                                        _agenda_slot_row,
                                    ),
                                    _agenda_pagination(
                                        page=AdminAgendaPreviewState.slot_page,
                                        total=AdminAgendaPreviewState.slot_total_pages,
                                        on_previous=AdminAgendaPreviewState.previous_slot_page,
                                        on_next=AdminAgendaPreviewState.next_slot_page,
                                    ),
                                    role="list", spacing="2", align="stretch",
                                    width="100%", margin_top="1rem",
                                ),
                                rx.text(
                                    "Nenhum horário cadastrado para este dia e profissional.",
                                    size="2", color="var(--vitta-text-muted)",
                                    padding="1.2rem 0",
                                ),
                            ),
                        ),
                    ),
                    columns=rx.breakpoints(initial="1", lg="1.05fr 1fr"),
                    gap="1rem", width="100%", align_items="start",
                ),
                section_panel(
                    rx.flex(
                        rx.heading("Consultas do dia", size="4"),
                        rx.badge(
                            AdminAgendaPreviewState.day_consultations.length(),
                            " consultas",
                            color_scheme="gray", variant="soft",
                        ),
                        justify="between", align="center", gap="3", width="100%",
                    ),
                    rx.cond(
                        AdminAgendaPreviewState.is_loading,
                        rx.center(rx.spinner(size="3"), min_height="5rem"),
                        rx.cond(
                            AdminAgendaPreviewState.day_consultations.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    AdminAgendaPreviewState.paginated_day_consultations,
                                    _agenda_consultation_row,
                                ),
                                _agenda_pagination(
                                    page=AdminAgendaPreviewState.consultation_page,
                                    total=AdminAgendaPreviewState.consultation_total_pages,
                                    on_previous=AdminAgendaPreviewState.previous_consultation_page,
                                    on_next=AdminAgendaPreviewState.next_consultation_page,
                                ),
                                role="list", spacing="2", align="stretch",
                                width="100%", margin_top="0.8rem",
                            ),
                            rx.text(
                                "Nenhuma consulta encontrada neste período.",
                                size="2", color="var(--vitta-text-muted)",
                                padding="0.9rem 0",
                            ),
                        ),
                    ),
                ),
                spacing="4", width="100%", align="stretch",
            ),
            rx.fragment(),
        ),
        spacing="4", align="stretch", width="100%",
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
                rx.text("Histórico clínico", font_weight="750", size="2"),
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
                empty_state(
                    "file_text",
                    "Sem histórico clínico concluído",
                    "Este paciente ainda não possui Atendimento clínico persistido em Consulta concluída.",
                ),
            ),
        ),
        margin_top="0.9rem",
        width="100%",
    )


def patients_preview() -> rx.Component:
    """Paginated read-only patient browser with operational and clinical history."""
    return rx.vstack(
        page_header(
            "Cadastros",
            "Pacientes",
            "Pesquise pacientes persistidos e consulte histórico operacional e clínico real em modo local de QA.",
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
                    _admin_clinical_history_panel(),
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
