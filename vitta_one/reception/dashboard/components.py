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
                    "Nenhuma consulta encontrada",
                    "Não há consultas para os filtros selecionados neste dia.",
                    min_height="10rem",
                    padding="1.25rem",
                ),
            ),
        ),
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
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="start", sm="center"),
            gap="0.85rem",
            width="100%",
            class_name="vitta-reception-day-pagination",
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
    return rx.box(
        rx.text("OPERAÇÃO DO DIA", class_name="vitta-section-kicker"),
        rx.heading(
            "Recepção — Operação do Dia",
            size="7",
            line_height="1.12",
            letter_spacing="-0.035em",
            font_family="var(--vitta-font-display)",
            margin_top="0.35rem",
            class_name="vitta-reception-day-title",
        ),
        rx.vstack(
            rx.text(S.clinic_date_label, font_weight="650", class_name="vitta-reception-day-date"),
            rx.text(
                "Última atualização: ", S.last_updated, size="1",
                color="var(--vitta-text-subtle)", class_name="vitta-reception-day-updated",
            ),
            align="start", spacing="1", role="status", aria_live="polite",
            class_name="vitta-reception-day-date-group",
        ),
        class_name="vitta-reception-day-header",
    )


def _reception_day_toolbar() -> rx.Component:
    return rx.box(
        rx.el.form(
            rx.flex(
                rx.box(
                    rx.box(
                        rx.icon("search", size=17, aria_hidden="true"),
                        position="absolute", left="0.8rem", top="50%",
                        transform="translateY(-50%)", color="var(--vitta-text-subtle)",
                        pointer_events="none",
                    ),
                    rx.el.input(
                        id="reception-day-search", name="query", type="search",
                        value=S.search_query, on_change=S.update_search_query,
                        placeholder="Nome, tel. ou CPF", auto_complete="off", max_length=100,
                        class_name="vitta-reception-day-search-input",
                        aria_label="Localizar paciente nas consultas de hoje por nome, telefone ou CPF",
                    ),
                    position="relative", min_width="0",
                    class_name="vitta-reception-day-search-control",
                ),
                rx.button(
                    "Buscar", type="submit", color_scheme="teal", variant="outline",
                    size="3", disabled=S.is_loading,
                    class_name="vitta-reception-day-search-button",
                ),
                direction=rx.breakpoints(initial="column", sm="row"),
                align=rx.breakpoints(initial="stretch", sm="center"),
                gap="0.55rem", width="100%",
            ),
            on_submit=S.apply_search, no_validate=True,
            class_name="vitta-reception-day-search-form",
        ),
        rx.box(
            field_label("Profissional", "reception-day-professional"),
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
        rx.hstack(
            rx.link(
                rx.icon("calendar_days", size=16), "Ir para Agenda",
                href="/recepcao/agenda", class_name="vitta-reception-day-secondary-action",
            ),
            rx.button(
                rx.icon("plus", size=16), "Nova consulta", type="button",
                on_click=rx.redirect("/recepcao/agenda"), color_scheme="teal",
                high_contrast=True, size="3",
                class_name="vitta-reception-day-primary-action",
            ),
            rx.button(
                rx.icon("refresh_cw", size=16),
                rx.text("Atualizar", class_name="vitta-reception-day-refresh-label"),
                type="button", on_click=S.refresh, variant="ghost", size="2",
                disabled=S.is_loading, aria_label="Atualizar consultas de hoje",
                title="Atualizar consultas de hoje", class_name="vitta-reception-day-refresh",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            align=rx.breakpoints(initial="stretch", md="center"),
            flex_wrap="wrap", gap="0.5rem", class_name="vitta-reception-day-actions",
        ),
        class_name="vitta-reception-day-toolbar",
    )


def reception_dashboard() -> rx.Component:
    return rx.vstack(
        rx.box(
            _reception_day_header(),
            _reception_day_toolbar(),
            class_name="vitta-reception-day-top",
        ),
        rx.cond(
            S.error_message != "",
            rx.callout(
                S.error_message, icon="triangle_alert", color_scheme="red", role="alert",
            ),
            rx.fragment(),
        ),
        feedback_region(
            ReceptionAgendaState.error_message,
            ReceptionAgendaState.success_message,
            "daily-appointment-action-feedback",
        ),
        rx.cond(
            S.is_loading & S.has_loaded,
            rx.callout(
                "Atualizando as consultas de hoje…", icon="refresh_cw",
                color_scheme="teal", role="status", aria_live="polite",
            ),
            rx.fragment(),
        ),
        rx.cond(
            S.has_loaded,
            section_panel(
                _appointments_table(), padding="0",
                class_name="vitta-reception-day-panel",
            ),
            rx.cond(
                S.is_loading,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text("Carregando consultas de hoje…", role="status", aria_live="polite"),
                    align="center", width="100%", padding="1.25rem",
                    class_name="vitta-reception-day-loading",
                ),
                rx.fragment(),
            ),
        ),
        reception_agenda_dialogs(),
        _appointment_details_dialog(),
        align="stretch", width="100%", spacing="4",
        class_name="vitta-reception-day-workspace",
    )
