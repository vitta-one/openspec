"""Daily operations table for the receptionist."""

import reflex as rx

from vitta_one.reception.dashboard.state import ReceptionDashboardState as S
from vitta_one.ui.appointment_components import consultation_status_badge
from vitta_one.ui.components import empty_state, field_label, section_panel


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
            rx.link(
                rx.icon("ellipsis_vertical", size=18),
                href="/recepcao/agenda",
                aria_label="Abrir Agenda para " + row["patient_name"] + " às " + row["time"],
                title="Abrir Agenda",
                class_name="vitta-reception-day-action",
            ),
            class_name="vitta-reception-day-action-cell",
            data_label="Ações",
        ),
        class_name="vitta-reception-day-row",
    )


def _appointments_table() -> rx.Component:
    return rx.box(
        rx.text(
            "Em telas estreitas, deslize horizontalmente para ver todas as colunas.",
            size="1",
            color="var(--vitta-text-subtle)",
            display=rx.breakpoints(initial="block", xl="none"),
            class_name="vitta-reception-day-scroll-hint",
        ),
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
                rx.el.tbody(
                    rx.cond(
                        S.appointments.length() > 0,
                        rx.foreach(S.appointments, _appointment_row),
                        rx.el.tr(
                            rx.el.td(
                                empty_state(
                                    "calendar",
                                    "Nenhuma consulta encontrada",
                                    "Não há consultas para os filtros selecionados neste dia.",
                                    min_height="10rem",
                                    padding="1.25rem",
                                ),
                                col_span=6,
                            )
                        ),
                    )
                ),
                class_name="vitta-reception-day-table",
            ),
            role="region",
            aria_label="Consultas de hoje; em telas estreitas, deslize horizontalmente para ver todas as colunas",
            tab_index=0,
            class_name="vitta-reception-day-table-scroll",
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


def reception_dashboard() -> rx.Component:
    return rx.vstack(
        rx.flex(
            rx.box(
                rx.text(
                    "OPERAÇÃO DA CLÍNICA",
                    class_name="vitta-section-kicker",
                ),
                rx.heading(
                    "Recepção — Operação do Dia",
                    size="7",
                    line_height="1.12",
                    letter_spacing="-0.035em",
                    font_family="var(--vitta-font-display)",
                    margin_top="0.35rem",
                    class_name="vitta-reception-day-title",
                ),
                min_width="0",
                class_name="vitta-reception-day-heading",
            ),
            rx.vstack(
                rx.text(
                    S.clinic_date_label,
                    font_weight="650",
                    class_name="vitta-reception-day-date",
                ),
                rx.text(
                    "Última atualização: ",
                    S.last_updated,
                    size="1",
                    color="var(--vitta-text-subtle)",
                    class_name="vitta-reception-day-updated",
                ),
                align="start",
                spacing="1",
                flex_shrink="0",
                role="status",
                aria_live="polite",
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="start", sm="end"),
            gap="1rem",
            width="100%",
            class_name="vitta-reception-day-header",
        ),
        rx.cond(
            S.error_message != "",
            rx.callout(
                S.error_message,
                icon="alert_triangle",
                color_scheme="red",
                role="alert",
            ),
            rx.fragment(),
        ),
        rx.cond(
            S.is_loading & S.has_loaded,
            rx.callout(
                "Atualizando as consultas de hoje…",
                icon="refresh_cw",
                color_scheme="teal",
                role="status",
                aria_live="polite",
            ),
            rx.fragment(),
        ),
        rx.flex(
            rx.el.form(
                rx.flex(
                    rx.box(
                        rx.box(
                            rx.icon("search", size=17, aria_hidden="true"),
                            position="absolute",
                            left="0.8rem",
                            top="50%",
                            transform="translateY(-50%)",
                            color="var(--vitta-text-subtle)",
                            pointer_events="none",
                        ),
                        rx.el.input(
                            id="reception-day-search",
                            name="query",
                            type="search",
                            value=S.search_query,
                            on_change=S.update_search_query,
                            placeholder="Nome, tel. ou CPF",
                            auto_complete="off",
                            max_length=100,
                            class_name="vitta-reception-day-search-input",
                            aria_label="Localizar paciente nas consultas de hoje por nome, telefone ou CPF",
                        ),
                        position="relative",
                        min_width="0",
                        class_name="vitta-reception-day-search-control",
                    ),
                    rx.button(
                        "Buscar",
                        type="submit",
                        color_scheme="teal",
                        variant="outline",
                        size="3",
                        disabled=S.is_loading,
                        class_name="vitta-reception-day-search-button",
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    align=rx.breakpoints(initial="stretch", sm="center"),
                    gap="0.55rem",
                    width="100%",
                ),
                on_submit=S.apply_search,
                no_validate=True,
                class_name="vitta-reception-day-search-form",
            ),
            rx.box(
                field_label("Profissional", "reception-day-professional"),
                rx.select.root(
                    rx.select.trigger(
                        id="reception-day-professional",
                        width="100%",
                        class_name="vitta-select-trigger",
                    ),
                    rx.select.content(
                        rx.select.item("Todos os profissionais", value="__all__"),
                        rx.foreach(
                            S.professional_options,
                            lambda item: rx.select.item(
                                item["label"], value=item["value"]
                            ),
                        ),
                        position="popper",
                    ),
                    value=S.professional_filter,
                    on_change=S.update_professional,
                    disabled=S.is_loading,
                    size="3",
                ),
                class_name="vitta-reception-day-professional-filter",
            ),
            rx.hstack(
                rx.link(
                    rx.icon("calendar_days", size=16),
                    "Ir para Agenda",
                    href="/recepcao/agenda",
                    class_name="vitta-reception-day-secondary-action",
                ),
                rx.button(
                    rx.icon("plus", size=16),
                    "Nova consulta",
                    type="button",
                    on_click=rx.redirect("/recepcao/agenda"),
                    color_scheme="teal",
                    high_contrast=True,
                    size="3",
                    class_name="vitta-reception-day-primary-action",
                ),
                rx.button(
                    rx.icon("refresh_cw", size=16),
                    rx.text("Atualizar", class_name="vitta-reception-day-refresh-label"),
                    type="button",
                    on_click=S.refresh,
                    variant="ghost",
                    size="2",
                    disabled=S.is_loading,
                    aria_label="Atualizar consultas de hoje",
                    title="Atualizar consultas de hoje",
                    class_name="vitta-reception-day-refresh",
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                align=rx.breakpoints(initial="stretch", md="center"),
                flex_wrap="wrap",
                gap="0.5rem",
                class_name="vitta-reception-day-actions",
            ),
            direction=rx.breakpoints(initial="column", xl="row"),
            align=rx.breakpoints(initial="stretch", xl="end"),
            gap="0.75rem",
            width="100%",
            class_name="vitta-reception-day-toolbar",
        ),
        rx.cond(
            S.has_loaded,
            section_panel(
                _appointments_table(),
                padding="0",
                class_name="vitta-reception-day-panel",
            ),
            rx.cond(
                S.is_loading,
                rx.hstack(
                    rx.spinner(size="2"),
                    rx.text(
                        "Carregando consultas de hoje…",
                        role="status",
                        aria_live="polite",
                    ),
                    align="center",
                    width="100%",
                    padding="1.25rem",
                    class_name="vitta-reception-day-loading",
                ),
                rx.fragment(),
            ),
        ),
        align="stretch",
        width="100%",
        spacing="5",
        class_name="vitta-reception-day-workspace",
    )
