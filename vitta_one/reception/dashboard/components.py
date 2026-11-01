"""Daily operations table for the receptionist."""

import reflex as rx

from vitta_one.appointment_scheduling.state import ReceptionAgendaState
from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
from vitta_one.ui.appointment_components import (
    consultation_status_badge,
    reception_agenda_dialogs,
)
from vitta_one.ui.components import empty_state, feedback_region, field_label, section_panel


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
            rx.text(
                row["time"],
                font_weight="700",
                class_name="vitta-tabular vitta-reception-day-time",
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
                rx.text(
                    row["patient_phone"],
                    size="1",
                    color="var(--vitta-text-muted)",
                    line_height="1.35",
                ),
                align="start",
                spacing="1",
                min_width="0",
            ),
            class_name="vitta-reception-day-patient",
            data_label="Paciente",
        ),
        rx.el.td(
            rx.text(
                row["professional_name"],
                line_height="1.4",
                overflow_wrap="anywhere",
            ),
            class_name="vitta-reception-day-professional",
            data_label="Profissional",
        ),
        rx.el.td(
            rx.text(
                row["specialty_name"],
                color="var(--vitta-text-muted)",
                line_height="1.4",
                overflow_wrap="anywhere",
            ),
            class_name="vitta-reception-day-specialty",
            data_label="Especialidades",
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
            _appointment_action_menu(row),
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
                                rx.el.th("Especialidades", scope="col"),
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
                    min_height="10rem",
                    padding="1.25rem",
                ),
            ),
        ),
        rx.cond(
            S.total_count > 0,
            rx.flex(
            rx.text(
                "Exibindo ",
                S.showing_start,
                "–",
                S.showing_end,
                " de ",
                S.total_count,
                " consultas de hoje",
                size="2",
                color="var(--vitta-text-muted)",
                role="status",
                aria_live="polite",
            ),
            rx.cond(
                S.total_pages > 1,
                rx.hstack(
                rx.button(
                    "‹ Anterior",
                    type="button",
                    on_click=S.previous_page,
                    variant="soft",
                    size="2",
                    disabled=(S.current_page <= 1) | S.is_loading,
                    aria_label="Página anterior",
                ),
                rx.text(
                    S.page_label,
                    size="2",
                    font_weight="700",
                    class_name="vitta-tabular",
                    aria_label="Página atual",
                ),
                rx.button(
                    "Próxima ›",
                    type="button",
                    on_click=S.next_page,
                    variant="soft",
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
                "Recepção", size="7",
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
            align="start", spacing="2", min_width="0",
        ),
        rx.vstack(
            rx.hstack(
                rx.link(
                    rx.icon("plus", size=16), "Nova consulta",
                    href="/recepcao/agenda/nova", class_name="vitta-primary-action",
                ),
                rx.button(
                    rx.cond(
                        S.is_loading,
                        rx.spinner(size="1"),
                        rx.icon("refresh_cw", size=16),
                    ),
                    rx.cond(S.is_loading, "Atualizando...", "Atualizar dados"),
                    type="button", on_click=S.refresh, variant="outline",
                    size="3", disabled=S.is_loading,
                    aria_label="Atualizar dados da Recepção",
                ),
                align="center", spacing="2", flex_wrap="wrap",
            ),
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
            align=rx.breakpoints(initial="start", md="end"), spacing="2",
        ),
        direction=rx.breakpoints(initial="column", md="row"),
        align=rx.breakpoints(initial="start", md="center"),
        justify="between", gap="4", width="100%",
        class_name="vitta-reception-day-header",
    )


def _reception_day_toolbar() -> rx.Component:
    """Search and professional filter only the daily appointment list."""
    return rx.grid(
        rx.el.form(
            field_label("Buscar nas consultas de hoje", "reception-day-search"),
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
                    ),
                    position="relative", min_width="0",
                    class_name="vitta-reception-day-search-control",
                ),
                rx.button(
                    "Buscar", type="submit", variant="outline", color_scheme="teal",
                    size="3", disabled=S.is_loading,
                    class_name="vitta-reception-day-search-button",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="2", width="100%", margin_top="0.4rem",
            ),
            on_submit=S.apply_search, no_validate=True,
            class_name="vitta-reception-day-search-form",
        ),
        rx.box(
            field_label("Filtrar profissional", "reception-day-professional"),
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
        rx.vstack(
            rx.flex(
                rx.text(label, font_weight="700", color="var(--vitta-text-muted)", size="2"),
                rx.icon(icon_name, size=19, color="var(--vitta-primary)"),
                justify="between", align="center", gap="2", width="100%",
            ),
            rx.heading(value, size="7", color="var(--vitta-text)", class_name="vitta-tabular"),
            rx.text(description, size="1", color="var(--vitta-text-muted)"),
            spacing="2", align="stretch", width="100%",
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
                          "Horários anteriores ainda sem check-in", "clock", "/recepcao/agenda"),
        _reception_metric("Concluídos hoje", S.overview_completed,
                          "Atendimentos finalizados", "circle_check", "/recepcao/fila"),
        columns=rx.breakpoints(initial="1", sm="2", lg="3", xl="5"),
        gap="3", width="100%",
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
                rx.link(rx.icon("plus", size=17), "Agendar consulta",
                        href="/recepcao/agenda/nova", class_name="vitta-context-link"),
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
                    rx.box(
                        rx.text(
                            "Indicadores gerais da clínica: consultas e conclusões "
                            "consideram hoje; espera e atendimento mostram a fila atual. "
                            "Os filtros abaixo alteram apenas a tabela.",
                            size="2", color="var(--vitta-text-muted)",
                            margin_bottom="0.75rem",
                        ),
                        reception_overview_cards(), width="100%",
                    ),
                    section_panel(
                        rx.vstack(
                            rx.flex(
                                rx.vstack(
                                    rx.heading("Consultas do dia", size="5"),
                                    rx.text(
                                        "Agendamentos do dia, com situação e ações disponíveis.",
                                        size="2", color="var(--vitta-text-muted)",
                                    ),
                                    align="start", spacing="1",
                                ),
                                rx.hstack(
                                    rx.link(
                                        "Novo paciente", href="/recepcao/pacientes/novo",
                                        class_name="vitta-context-link",
                                    ),
                                    rx.link(
                                        "Ver fila de espera", href="/recepcao/fila",
                                        class_name="vitta-context-link",
                                    ),
                                    spacing="2", flex_wrap="wrap",
                                ),
                                direction=rx.breakpoints(initial="column", md="row"),
                                justify="between",
                                align=rx.breakpoints(initial="start", md="center"),
                                gap="3", width="100%",
                            ),
                            _reception_day_toolbar(),
                            _appointments_table(),
                            spacing="4", align="stretch", width="100%",
                        ),
                    ),
                ),
                rx.fragment(),
            ),
        ),
        _appointment_details_dialog(),
        reception_agenda_dialogs(),
        rx.moment(interval=60000, on_change=S.tick, display="none"),
        align="stretch", width="100%", spacing="4",
        class_name="vitta-reception-overview vitta-reception-operations",
    )
