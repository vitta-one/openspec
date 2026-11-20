"""Daily operations table for the receptionist."""

import reflex as rx

from vitta_one.appointment_scheduling.state import ReceptionAgendaState
from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
from vitta_one.ui.appointment_components import (
    consultation_status_badge,
    reception_agenda_dialogs,
)
from vitta_one.ui.components import error_banner, empty_state, feedback_region, field_label, section_panel
from vitta_one.patient_queue.state import ReceptionQueueState


def _appointment_action_menu(row) -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis_vertical", size=18),
                type="button",
                variant="ghost",
                size="2",
                aria_label="Ações para " + row["patient_name"] + " às " + row["time"],
                title="Ações da consulta",
                class_name="vitta-reception-day-action",
            ),
            as_child=True,
        ),
        rx.menu.content(
            rx.menu.item(
                "Ver detalhes operacionais",
                on_select=S.show_appointment_details(row["id"]),
                class_name="vitta-reception-day-menu-item",
            ),
            rx.cond(
                row["status_value"] == "AGENDADA",
                rx.fragment(
                    rx.menu.item(
                        "Confirmar chegada",
                        on_select=ReceptionAgendaState.open_arrival_from_daily_operations(
                            row["id"]
                        ),
                        class_name="vitta-reception-day-menu-item",
                    ),
                    rx.menu.item(
                        "Reagendar",
                        on_select=ReceptionAgendaState.open_reschedule_from_daily_operations(
                            row["id"]
                        ),
                        class_name="vitta-reception-day-menu-item",
                    ),
                    rx.menu.item(
                        "Cancelar consulta",
                        on_select=ReceptionAgendaState.open_cancel_from_daily_operations(
                            row["id"]
                        ),
                        class_name="vitta-reception-day-menu-item vitta-reception-day-menu-danger",
                    ),
                ),
                rx.fragment(),
            ),
            rx.cond(
                row["status_value"] == "CONFIRMADA",
                rx.menu.item(
                    "Abrir fila de espera",
                    on_select=rx.redirect("/recepcao/fila"),
                    class_name="vitta-reception-day-menu-item",
                ),
                rx.fragment(),
            ),
            rx.menu.separator(),
            rx.menu.item(
                "Abrir Agenda",
                on_select=rx.redirect("/recepcao/agenda"),
                class_name="vitta-reception-day-menu-item",
            ),
        ),
        class_name="vitta-reception-day-menu",
    )


def _appointment_row(row) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.hstack(
                rx.icon("clock_3", size=16, color="var(--vitta-text-muted)", aria_hidden="true"),
                rx.text(
                    row["time"],
                    font_weight="700",
                    class_name="vitta-tabular vitta-reception-day-time",
                ),
                spacing="2", align="center",
            ),
            class_name="vitta-reception-day-time-cell",
            data_label="Horário",
        ),
        rx.el.td(
            rx.vstack(
                rx.text(
                    row["patient_name"],
                    font_weight="700",
                    line_height="1.35",
                    overflow_wrap="anywhere",
                ),
                align="start",
                spacing="1",
                min_width="0",
            ),
            class_name="vitta-reception-day-patient",
            data_label="Paciente",
        ),
        rx.el.td(
            rx.vstack(
                rx.text(row["professional_name"], line_height="1.35", overflow_wrap="anywhere"),
                align="start", spacing="1", min_width="0",
            ),
            class_name="vitta-reception-day-professional",
            data_label="Profissional",
        ),
        rx.el.td(
            consultation_status_badge(
                row["status_value"],
                row["status_label"],
                class_name="vitta-reception-day-status",
            ),
            class_name="vitta-reception-day-status-cell",
            data_label="Status",
        ),
        rx.el.td(
            rx.hstack(
                rx.button(
                    rx.icon("eye", size=17), type="button", variant="outline",
                    color_scheme="teal", size="2",
                    aria_label="Ver detalhes de " + row["patient_name"] + " às " + row["time"],
                    on_click=S.show_appointment_details(row["id"]),
                    class_name="vitta-reception-day-view-action",
                ),
                _appointment_action_menu(row),
                spacing="1", align="center", justify="center",
            ),
            class_name="vitta-reception-day-action-cell",
            data_label="Ações",
        ),
        class_name="vitta-reception-day-row",
    )


def _appointment_card(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(
                    row["time"],
                    font_weight="800",
                    class_name="vitta-tabular vitta-reception-day-card-time",
                ),
                rx.text(
                    row["patient_name"],
                    font_weight="750",
                    line_height="1.35",
                    overflow_wrap="anywhere",
                ),
                rx.text(
                    row["patient_phone"],
                    size="1",
                    color="var(--vitta-text-muted)",
                    margin_top="0.2rem",
                ),
                min_width="0",
            ),
            rx.vstack(
                consultation_status_badge(
                    row["status_value"],
                    row["status_label"],
                    class_name="vitta-reception-day-status",
                ),
                _appointment_action_menu(row),
                align="end",
                spacing="2",
                flex_shrink="0",
            ),
            justify="between",
            align="start",
            gap="0.6rem",
            width="100%",
        ),
        rx.box(
            rx.text(
                "Profissional",
                size="1",
                color="var(--vitta-text-subtle)",
                font_weight="650",
            ),
            rx.text(row["professional_name"], size="2", overflow_wrap="anywhere"),
            margin_top="0.75rem",
        ),
        rx.box(
            rx.text(
                "Especialidades",
                size="1",
                color="var(--vitta-text-subtle)",
                font_weight="650",
            ),
            rx.text(
                row["specialty_name"],
                size="2",
                color="var(--vitta-text-muted)",
                overflow_wrap="anywhere",
            ),
            margin_top="0.55rem",
        ),
        class_name="vitta-reception-day-card",
    )


def _appointments_table() -> rx.Component:
    return rx.box(
        rx.cond(
            S.appointments.length() > 0,
            rx.fragment(
                rx.box(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th("Horário", scope="col"),
                                rx.el.th("Paciente", scope="col"),
                                rx.el.th("Profissional", scope="col"),
                                rx.el.th("Status", scope="col"),
                                rx.el.th("Ações", scope="col"),
                            )
                        ),
                        rx.el.tbody(rx.foreach(S.appointments, _appointment_row)),
                        class_name="vitta-reception-day-table",
                    ),
                    role="region",
                    aria_label="Consultas de hoje",
                    tab_index=0,
                    class_name="vitta-reception-day-table-scroll",
                ),
                rx.vstack(
                    rx.foreach(S.appointments, _appointment_card),
                    align="stretch",
                    spacing="3",
                    class_name="vitta-reception-day-cards",
                ),
            ),
            rx.cond(
                S.has_active_filters,
                empty_state(
                    "search",
                    "Nenhuma consulta combina com estes filtros",
                    "Altere os termos de busca ou limpe os filtros para ver novamente as consultas do dia.",
                    rx.button(
                        "Limpar filtros",
                        type="button",
                        variant="soft",
                        on_click=S.clear_filters,
                        disabled=S.is_loading,
                    ),
                    min_height="10rem",
                    padding="1.25rem",
                ),
                empty_state(
                    "calendar",
                    "Nenhuma consulta agendada hoje",
                    "A agenda do dia está vazia. Outras atividades da fila podem continuar em andamento.",
                    rx.button(
                        "Agendar primeira consulta",
                        type="button", variant="outline", color_scheme="teal",
                        on_click=ReceptionAgendaState.open_booking,
                    ),
                    min_height="10rem",
                    padding="1.25rem",
                ),
            ),
        ),
        rx.cond(
            S.total_count > 0,
            rx.flex(
            rx.text(
                "Mostrando ",
                S.showing_end,
                " de ",
                S.total_count,
                " consultas",
                size="2",
                color="var(--vitta-text-muted)",
                role="status",
                aria_live="polite",
            ),
            rx.cond(
                S.total_pages > 1,
                rx.hstack(
                rx.button(
                    rx.icon("chevron_left", size=17),
                    type="button",
                    on_click=S.previous_page,
                    variant="outline",
                    size="2",
                    disabled=(S.current_page <= 1) | S.is_loading,
                    aria_label="Página anterior",
                ),
                rx.foreach(
                    S.page_numbers,
                    lambda page: rx.button(
                        page,
                        type="button",
                        on_click=S.go_to_page(page),
                        variant="outline",
                        color_scheme="teal",
                        size="2",
                        disabled=S.is_loading,
                        aria_current=rx.cond(S.current_page == page, "page", "false"),
                        class_name="vitta-reception-page-number",
                    ),
                ),
                rx.button(
                    rx.icon("chevron_right", size=17),
                    type="button",
                    on_click=S.next_page,
                    variant="outline",
                    size="2",
                    disabled=(S.current_page >= S.total_pages) | S.is_loading,
                    aria_label="Próxima página",
                ),
                align="center",
                spacing="2",
                flex_wrap="wrap",
                ),
                rx.fragment(),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="start", sm="center"),
            gap="0.85rem",
            width="100%",
            class_name="vitta-reception-day-pagination",
            ),
            rx.fragment(),
        ),
        class_name="vitta-reception-day-table-area",
    )


def _appointment_details_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Detalhes operacionais"),
            rx.dialog.description(
                "Resumo da consulta para a operação da Recepção. Nenhuma informação clínica é exibida.",
                margin_top="0.35rem",
                margin_bottom="1rem",
            ),
            rx.box(
                rx.text("Horário", size="1", color="var(--vitta-text-subtle)"),
                rx.text(S.details_time, font_weight="750", class_name="vitta-tabular"),
                class_name="vitta-reception-day-detail-row",
            ),
            rx.box(
                rx.text("Paciente", size="1", color="var(--vitta-text-subtle)"),
                rx.text(S.details_patient_name, font_weight="750", overflow_wrap="anywhere"),
                rx.text(S.details_patient_phone, size="2", color="var(--vitta-text-muted)"),
                class_name="vitta-reception-day-detail-row",
            ),
            rx.box(
                rx.text("Profissional", size="1", color="var(--vitta-text-subtle)"),
                rx.text(S.details_professional_name, overflow_wrap="anywhere"),
                class_name="vitta-reception-day-detail-row",
            ),
            rx.box(
                rx.text("Especialidades", size="1", color="var(--vitta-text-subtle)"),
                rx.text(S.details_specialty_name, overflow_wrap="anywhere"),
                class_name="vitta-reception-day-detail-row",
            ),
            rx.box(
                rx.text("Status", size="1", color="var(--vitta-text-subtle)"),
                consultation_status_badge(
                    S.details_status_value,
                    S.details_status_label,
                    class_name="vitta-reception-day-status",
                ),
                class_name="vitta-reception-day-detail-row",
            ),
            rx.dialog.close(
                rx.button("Fechar", type="button", variant="soft", margin_top="1rem")
            ),
            class_name="vitta-dialog-content",
            max_width="34rem",
        ),
        open=S.details_dialog_open,
        on_open_change=S.set_details_dialog_open,
    )


def _reception_day_header() -> rx.Component:
    """Compact reception heading with one primary action."""
    return rx.flex(
        rx.vstack(
            rx.text("OPERAÇÃO DO DIA", class_name="vitta-section-kicker"),
            rx.heading(
                "Recepção", size="6",
                font_family="var(--vitta-font-display)",
                class_name="vitta-reception-day-title",
            ),
            rx.text(
                "Acompanhe as consultas, chegadas e atendimentos do dia.",
                color="var(--vitta-text-muted)", size="2",
            ),
            rx.text(
                S.clinic_date_label, font_weight="650",
                class_name="vitta-reception-day-date",
            ),
            align="start", spacing="1", min_width="0",
        ),
        rx.vstack(
            rx.cond(
                S.has_loaded,
                rx.text(
                    "Última atualização: ", S.last_updated, size="1",
                    color="var(--vitta-text-muted)",
                    class_name="vitta-reception-day-updated",
                    role="status", aria_live="polite",
                ),
                rx.fragment(),
            ),
            _reception_quick_actions(),
            align=rx.breakpoints(initial="stretch", md="end"), spacing="1",
            min_width="0", class_name="vitta-reception-day-header-actions",
        ),
        direction=rx.breakpoints(initial="column", md="row"),
        align=rx.breakpoints(initial="start", md="center"),
        justify="between", gap="3", width="100%",
        class_name="vitta-reception-day-header",
    )


def _reception_day_toolbar() -> rx.Component:
    """Search and professional filter only the daily appointment list."""
    return rx.grid(
        rx.el.form(
            rx.el.label(
                "Buscar nas consultas de hoje", html_for="reception-day-search",
                class_name="vitta-sr-only",
            ),
            rx.flex(
                rx.box(
                    rx.box(
                        rx.icon("search", size=17, aria_hidden="true"),
                        position="absolute", left="0.8rem", top="50%",
                        transform="translateY(-50%)",
                        color="var(--vitta-text-subtle)", pointer_events="none",
                    ),
                    rx.el.input(
                        id="reception-day-search", name="query", type="search",
                        value=S.search_query, on_change=S.update_search_query,
                        placeholder="Nome, telefone ou CPF", auto_complete="off",
                        max_length=100, class_name="vitta-reception-day-search-input",
                        aria_label="Buscar paciente nas consultas de hoje",
                        aria_describedby="reception-day-search-help",
                    ),
                    position="relative", min_width="0",
                    class_name="vitta-reception-day-search-control",
                ),
                width="100%",
            ),
            rx.el.span(
                "Pressione Enter para aplicar a busca.",
                id="reception-day-search-help",
                class_name="vitta-sr-only",
            ),
            on_submit=S.apply_search, no_validate=True,
            class_name="vitta-reception-day-search-form",
        ),
        rx.box(
            rx.el.label(
                "Filtrar profissional", html_for="reception-day-professional",
                class_name="vitta-sr-only",
            ),
            rx.select.root(
                rx.select.trigger(
                    id="reception-day-professional", width="100%",
                    class_name="vitta-select-trigger",
                ),
                rx.select.content(
                    rx.select.item("Todos os profissionais", value="__all__"),
                    rx.foreach(
                        S.professional_options,
                        lambda item: rx.select.item(item["label"], value=item["value"]),
                    ),
                    position="popper",
                ),
                value=S.professional_filter, on_change=S.update_professional,
                disabled=S.is_loading, size="3",
            ),
            class_name="vitta-reception-day-professional-filter",
        ),
        columns=rx.breakpoints(initial="1", md="minmax(0, 1fr) minmax(13rem, 18rem)"),
        gap="3", width="100%", align="end",
        class_name="vitta-reception-day-toolbar",
    )


def _reception_metric(label: str, value, description: str, icon_name: str, href: str) -> rx.Component:
    return rx.link(
        rx.flex(
            rx.box(
                rx.icon(icon_name, size=21),
                class_name="vitta-reception-metric-icon",
            ),
            rx.vstack(
                rx.text(label, font_weight="650", color="var(--vitta-text-muted)", size="2"),
                rx.heading(value, size="6", color="var(--vitta-text)", class_name="vitta-tabular"),
                rx.text(description, size="1", color="var(--vitta-text-muted)"),
                spacing="0", align="start", width="100%", min_width="0",
            ),
            align="center", gap="0.8rem", width="100%", min_width="0",
        ),
        href=href,
        class_name="vitta-overview-card",
    )


def reception_overview_cards() -> rx.Component:
    """Real operational KPIs from the authorized receptionist overview service."""
    return rx.grid(
        _reception_metric("Consultas hoje", S.overview_scheduled,
                          "Exceto canceladas", "calendar_days", "/recepcao/agenda"),
        _reception_metric("Na espera", S.overview_waiting,
                          "Pacientes na fila", "users", "/recepcao/fila"),
        _reception_metric("Em atendimento", S.overview_attending,
                          "Atendimentos em curso", "stethoscope", "/recepcao/fila"),
        _reception_metric("Chegadas pendentes", S.overview_pending,
                          "Pacientes sem check-in", "clock", "/recepcao/agenda"),
        _reception_metric("Concluídos hoje", S.overview_completed,
                          "Atendimentos finalizados", "circle_check", "/recepcao/fila"),
        _reception_metric("Canceladas", S.overview_cancelled,
                          "Consultas canceladas hoje", "circle_x", "/recepcao/agenda"),
        columns=rx.breakpoints(initial="1", sm="2", lg="3", xl="6"),
        gap="3", width="100%",
    )


def _queue_preview_row(row) -> rx.Component:
    priority_badge = rx.match(
        row["priority"],
        ("VERMELHO", rx.badge(row["priority_label"], color_scheme="red", high_contrast=True)),
        ("AMARELO", rx.badge(row["priority_label"], color_scheme="amber", high_contrast=True)),
        rx.badge(row["priority_label"], color_scheme="green", high_contrast=True),
    )
    return rx.flex(
        rx.vstack(
            rx.text(row["patient_name"], size="2", font_weight="700", overflow_wrap="anywhere"),
            rx.text("Espera: ", row["wait_label"], size="1", color="var(--vitta-text-muted)"),
            align="start", spacing="1", min_width="0",
        ),
        priority_badge,
        align="center", justify="between", gap="2", width="100%",
        class_name="vitta-reception-preview-row",
    )


def _reception_queue_preview() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.heading("Fila de espera", size="4"),
                    rx.text(ReceptionQueueState.queue_count, " aguardando",
                            size="1", color="var(--vitta-text-muted)"),
                    align="start", spacing="0",
                ),
                rx.link("Abrir fila", href="/recepcao/fila", class_name="vitta-context-link"),
                justify="between", align="center", gap="2", width="100%",
            ),
            rx.cond(
                ReceptionQueueState.is_loading_queue,
                rx.center(rx.spinner(size="2"), rx.text("Atualizando fila…", size="1"),
                          gap="2", min_height="5rem", role="status"),
                rx.cond(
                    ReceptionQueueState.queue_load_error != "",
                    error_banner(ReceptionQueueState.queue_load_error),
                    rx.cond(
                        ReceptionQueueState.queue_count > 0,
                        rx.vstack(
                            rx.foreach(ReceptionQueueState.queue_preview_rows, _queue_preview_row),
                            spacing="0", align="stretch", width="100%",
                        ),
                        empty_state(
                            "users", "Fila vazia",
                            "Nenhum paciente está aguardando neste momento.",
                            rx.link("Adicionar à fila", href="/recepcao/fila/nova",
                                    class_name="vitta-context-link"),
                            min_height="7rem", padding="0.75rem",
                        ),
                    ),
                ),
            ),
            align="stretch", spacing="3", width="100%",
        ),
    )


def _upcoming_appointments_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.heading("Próximos atendimentos", size="4"),
                rx.link("Ver agenda", href="/recepcao/agenda", class_name="vitta-context-link"),
                align="center", justify="between", gap="2", width="100%",
            ),
            rx.cond(
                S.upcoming_appointments.length() > 0,
                rx.vstack(
                    rx.foreach(
                        S.upcoming_appointments,
                        lambda row: rx.flex(
                            rx.box(
                                rx.text(row["time"], font_weight="800", class_name="vitta-tabular"),
                                rx.text(row["date_label"], size="1", color="var(--vitta-text-muted)"),
                                min_width="3.5rem",
                            ),
                            rx.vstack(
                                rx.text(row["patient_name"], size="2", font_weight="700",
                                        overflow_wrap="anywhere"),
                                rx.text(row["professional_name"], size="1",
                                        color="var(--vitta-text-muted)", overflow_wrap="anywhere"),
                                align="start", spacing="0", min_width="0",
                            ),
                            align="center", gap="2", width="100%",
                            class_name="vitta-reception-preview-row vitta-reception-upcoming-row",
                        ),
                    ),
                    spacing="0", align="stretch", width="100%",
                ),
                rx.text("Não há consultas futuras registradas para os próximos sete dias.",
                        size="2", color="var(--vitta-text-muted)", padding_block="1rem"),
            ),
            align="stretch", spacing="2", width="100%",
        ),
        padding=".75rem .85rem",
        class_name="vitta-reception-upcoming-panel",
    )


def _operational_alerts_panel() -> rx.Component:
    return section_panel(
        rx.vstack(
            rx.heading("Alertas operacionais", size="4"),
            rx.cond(
                (S.overview_pending == 0) & (S.email_failed == 0),
                rx.text("Nenhum item requer revisão agora.", size="2",
                        color="var(--vitta-text-muted)"),
                rx.vstack(
                    rx.cond(
                        S.overview_pending > 0,
                        rx.link(
                            rx.hstack(
                                rx.icon("clock_alert", size=17),
                                rx.text(S.overview_pending,
                                        " consultas anteriores ainda sem check-in"),
                                gap="2", align="start",
                            ),
                            href="/recepcao/agenda",
                            class_name="vitta-operational-alert-link",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        S.email_failed > 0,
                        rx.link(
                            rx.hstack(
                                rx.icon("mail_x", size=17),
                                rx.text(S.email_failed, " falhas de envio para revisar"),
                                gap="2", align="start",
                            ),
                            href="/recepcao#notificacoes",
                            class_name="vitta-operational-alert-link",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2", align="stretch", width="100%",
                ),
            ),
            align="stretch", spacing="3", width="100%",
        ),
    )


def _reception_quick_actions() -> rx.Component:
    return section_panel(
        rx.flex(
            rx.hstack(
                rx.icon("zap", size=18, color="var(--vitta-primary)"),
                rx.text("Ações rápidas", font_weight="750", size="2", white_space="nowrap"),
                align="center", gap="2", class_name="vitta-reception-quick-heading",
            ),
            rx.flex(
            rx.button(
                rx.icon("calendar_plus", size=17), "Nova consulta",
                type="button", color_scheme="teal", high_contrast=True,
                on_click=ReceptionAgendaState.open_booking,
                disabled=ReceptionAgendaState.is_submitting,
                class_name="vitta-reception-quick-link vitta-reception-quick-link--primary",
            ),
            rx.link(
                rx.hstack(rx.icon("user_round_plus", size=16), rx.text("Novo paciente"), gap="2", align="center"),
                href="/recepcao/pacientes/novo", class_name="vitta-reception-quick-link",
            ),
            rx.link(
                rx.hstack(rx.icon("list_ordered", size=16), rx.text("Ver fila de espera"), gap="2", align="center"),
                href="/recepcao/fila", class_name="vitta-reception-quick-link",
            ),
            rx.button(
                rx.cond(S.is_loading, rx.spinner(size="1"), rx.icon("refresh_cw", size=16)),
                rx.cond(S.is_loading, "Atualizando...", "Atualizar dados"),
                type="button", on_click=S.refresh, variant="outline",
                disabled=S.is_loading, class_name="vitta-reception-quick-link",
                aria_label="Atualizar dados da Recepção",
            ),
            gap="2", align="center", flex_wrap="wrap", justify="end",
            min_width="0", class_name="vitta-reception-quick-actions",
            ),
            align="center", justify="between", gap="3", flex_wrap="wrap",
            width="100%", class_name="vitta-reception-quick-toolbar",
        ),
        padding=".55rem .65rem",
        class_name="vitta-reception-quick-panel",
    )


def reception_email_metrics_panel() -> rx.Component:
    """Show provider acceptance and authenticated delivery as separate facts."""
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.heading("Confirmações por e-mail", size="4"),
                    rx.text(
                        "Envios recentes. Aceito pelo provedor não confirma a entrega.",
                        size="2",
                        color="var(--vitta-text-muted)",
                        max_width="30rem",
                        class_name="vitta-reception-email-description",
                    ),
                    align="start",
                    spacing="1",
                    min_width="0",
                    class_name="vitta-reception-email-copy",
                ),
                rx.link(
                    "Consultar envios", href="/recepcao#notificacoes",
                    class_name="vitta-context-link vitta-reception-email-link",
                ),
                justify="between",
                align="center",
                gap="3",
                flex_wrap="wrap",
                width="100%",
            ),
            rx.grid(
                _email_metric("Aceitos pelo Resend", S.email_accepted, "mail_check"),
                _email_metric("Entregues", S.email_delivered, "circle_check"),
                _email_metric("Pendentes / indeterminados", S.email_pending, "clock_3"),
                _email_metric("Falhas", S.email_failed, "circle_x"),
                columns=rx.breakpoints(initial="1", sm="2", xl="4"),
                gap="3",
                width="100%",
            ),
            align="stretch",
            spacing="3",
            width="100%",
            class_name="vitta-reception-email-metrics",
        )
    )


def _email_metric(label: str, value, icon_name: str) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(rx.icon(icon_name, size=18), class_name="vitta-email-metric-icon"),
            rx.vstack(
                rx.text(label, size="1", font_weight="650", color="var(--vitta-text-muted)"),
                rx.text(value, size="5", font_weight="800", class_name="vitta-tabular"),
                spacing="0",
                align="start",
            ),
            gap="2",
            align="center",
        ),
        class_name="vitta-email-metric",
    )


def _agenda_day_card(day) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(day["day_label"], size="2", font_weight="700",
                    color="var(--vitta-text-muted)"),
            rx.heading(day["date_label"], size="5"),
            rx.separator(),
            rx.cond(day["entries"].length() > 0,
                rx.vstack(
                    rx.foreach(day["entries"], lambda item: rx.box(
                        rx.text(item["time"], font_weight="800", color="#115e59",
                                class_name="vitta-tabular", size="2"),
                        rx.text(item["patient_name"], size="2", font_weight="650"),
                        rx.text(item["professional_name"], size="1",
                                color="var(--vitta-text-muted)"),
                        class_name="vitta-agenda-event",
                    )),
                    spacing="2", align="stretch", width="100%",
                ),
                rx.text("Sem consultas", size="1", color="var(--vitta-text-muted)",
                        padding_top="0.75rem"),
            ),
            spacing="3", align="stretch", width="100%",
        ),
        class_name="vitta-agenda-day",
    )


def reception_week_calendar() -> rx.Component:
    """Seven-day read-only appointment calendar; scheduling/actions remain below."""
    return section_panel(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.heading("Visão semanal", size="5"),
                    rx.text("Próximos sete dias da clínica. Os horários vêm das consultas salvas.",
                            size="2", color="var(--vitta-text-muted)"),
                    spacing="2", align="start",
                ),
                rx.button(
                    rx.icon("plus", size=17), "Agendar consulta",
                    type="button", variant="outline", color_scheme="teal",
                    on_click=ReceptionAgendaState.open_booking,
                ),
                justify="between", align="center", flex_wrap="wrap", gap="3", width="100%",
            ),
            rx.box(
                rx.grid(
                    rx.foreach(S.calendar_week, _agenda_day_card),
                    columns="7", gap="2",
                    class_name="vitta-agenda-week-grid",
                ),
                class_name="vitta-agenda-week-scroll",
                width="100%", overflow_x="auto",
            ),
            spacing="4", align="stretch", width="100%",
        )
    )


def reception_dashboard() -> rx.Component:
    """Operational reception home with real daily appointments and metrics."""
    return rx.vstack(
        _reception_day_header(),
        rx.cond(
            S.error_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("triangle_alert", size=18), rx.text(S.error_message),
                    spacing="2", align="center",
                ),
                role="alert", padding="0.9rem 1rem",
                border="1px solid var(--vitta-danger-border)",
                border_radius="var(--vitta-radius-control)",
                background="var(--vitta-danger-soft)",
                color="var(--vitta-danger)", width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            S.is_loading & ~S.has_loaded,
            rx.center(
                rx.spinner(size="3"),
                rx.text("Carregando operação do dia...", size="2"),
                gap="3", min_height="12rem", width="100%",
                role="status", aria_live="polite",
            ),
            rx.cond(
                S.has_loaded,
                rx.fragment(
                    reception_overview_cards(),
                    rx.grid(
                        section_panel(
                            rx.vstack(
                                rx.flex(
                                    rx.hstack(
                                        rx.box(
                                            rx.icon("calendar_days", size=20, aria_hidden="true"),
                                            class_name="vitta-reception-section-icon",
                                        ),
                                        rx.vstack(
                                            rx.heading("Consultas de hoje", size="4"),
                                            rx.text(
                                                "Agendamentos do dia, com situação e ações disponíveis.",
                                                size="1", color="var(--vitta-text-muted)",
                                            ),
                                            align="start", spacing="1", min_width="0",
                                        ),
                                        align="center", spacing="3", min_width="0",
                                        class_name="vitta-reception-day-panel-heading",
                                    ),
                                    _reception_day_toolbar(),
                                    direction=rx.breakpoints(initial="column", md="row"),
                                    justify="between",
                                    align=rx.breakpoints(initial="stretch", md="center"),
                                    gap="3", width="100%",
                                    class_name="vitta-reception-day-panel-header",
                                ),
                                _appointments_table(),
                                spacing="3", align="stretch", width="100%",
                            ),
                            padding=".65rem .85rem",
                            class_name="vitta-reception-appointments-panel",
                        ),
                    rx.vstack(
                        _reception_queue_preview(),
                        _upcoming_appointments_panel(),
                        align="stretch", spacing="3", width="100%",
                    ),
                    columns=rx.breakpoints(
                        initial="1", xl="minmax(0, 2fr) minmax(19rem, 0.9fr)"
                    ),
                    gap="3", align="start", width="100%",
                    class_name="vitta-reception-dashboard-grid",
                    ),
                    rx.grid(
                        _operational_alerts_panel(),
                        reception_email_metrics_panel(),
                        columns=rx.breakpoints(
                            initial="1", xl="minmax(0, 1fr) minmax(0, 1.15fr)"
                        ),
                        gap="3", align="stretch", width="100%",
                        class_name="vitta-reception-dashboard-footer",
                    ),
                ),
                rx.fragment(),
            ),
        ),
        _appointment_details_dialog(),
        reception_agenda_dialogs(),
        rx.moment(interval=60000, on_change=S.tick, display="none"),
        align="stretch", width="100%", spacing="3",
        class_name="vitta-reception-overview vitta-reception-operations",
    )
