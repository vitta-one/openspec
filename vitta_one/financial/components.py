"""Financial workspace using the existing Vitta-One shell and visual tokens."""
import reflex as rx

from vitta_one.auth.state import AuthState
from vitta_one.ui.components import page_header, section_panel
from .state import FinancialState as S
from .application import LABELS
from vitta_one.notifications.operations import operations_panel


def field(label: str, control: rx.Component):
    return rx.vstack(
        rx.text(label, size="1", font_weight="600"),
        control,
        spacing="1",
        align="stretch",
        width="100%",
    )


def _finance_metric(title: str, value, icon: str, tone: str) -> rx.Component:
    return rx.flex(
        rx.box(rx.icon(icon, size=21), class_name=f"vitta-finance-metric-icon vitta-finance-metric-icon--{tone}"),
        rx.vstack(
            rx.text(title, size="2", color="var(--vitta-text-muted)"),
            rx.text(value, size="5", font_weight="750", class_name="vitta-tabular"),
            spacing="0",
            align="start",
            min_width="0",
        ),
        align="center",
        gap="1.25rem",
        class_name="vitta-finance-metric",
    )


def status_select():
    return rx.select.root(
        rx.select.trigger(
            placeholder="Todas as situações",
            class_name="vitta-select-trigger",
            width="100%",
        ),
        rx.select.content(
            rx.select.item("Todas as situações", value="ALL"),
            *[rx.select.item(label, value=code) for code, label in LABELS.items()],
        ),
        name="status",
        default_value="ALL",
        width="100%",
    )


def charge_row(row):
    return rx.table.row(
        rx.table.row_header_cell(rx.text(row["patient"], font_weight="650")),
        rx.table.cell(rx.text("Consulta ", row["consultation"], size="2")),
        rx.table.cell(rx.text(row["value"], font_weight="650")),
        rx.table.cell(rx.text(row["due"], class_name="vitta-tabular")),
        rx.table.cell(rx.badge(row["status"], color_scheme="gray", variant="soft")),
        rx.table.cell(
            rx.button(
                "Ver detalhes", on_click=S.show(row["id"]),
                variant="outline", disabled=S.busy,
            ),
        ),
        class_name="vitta-finance-charge-row",
    )


def _finance_charge_empty_state() -> rx.Component:
    return rx.center(
        rx.flex(
            rx.box(
                rx.icon("wallet", size=22, aria_hidden="true"),
                class_name="vitta-empty-icon vitta-finance-charge-empty-icon",
                aria_hidden="true",
            ),
            rx.vstack(
                rx.text("Nenhuma cobrança encontrada", size="2", font_weight="700"),
                rx.text(
                    "Ajuste os filtros ou emita uma nova cobrança.",
                    size="1", color="var(--vitta-text-muted)",
                ),
                spacing="1", align="start", min_width="0",
            ),
            align="center", gap="1.25rem", min_width="0",
            role="status", aria_live="polite",
        ),
        min_height="5.5rem", padding=".5rem 1rem", width="100%",
        class_name="vitta-empty-state vitta-finance-charge-empty-state",
    )


def _evolution_row(row):
    return rx.grid(
        rx.text(row["day"], size="2", class_name="vitta-tabular"),
        rx.box(
            rx.box(
                width=row["bar_percent"].to(str) + "%",
                class_name="vitta-finance-chart-bar",
            ),
            class_name="vitta-finance-chart-track",
            aria_hidden="true",
        ),
        rx.text(
            row["value"],
            size="2",
            font_weight="700",
            class_name="vitta-tabular",
            text_align="right",
        ),
        columns="minmax(5rem, 6rem) minmax(0, 1fr) minmax(6rem, 8rem)",
        gap=".75rem", align="center", width="100%",
        class_name="vitta-finance-chart-row",
        role="listitem",
    )


def finance_content():
    return rx.vstack(
        page_header(
            "Vitta One", "Financeiro", "Cobranças e recebimentos · Asaas Sandbox",
            show_art=True, art_source="/clinic-finance-hero.png",
        ),
        rx.grid(
            _finance_metric("Recebido", S.received, "wallet", "green"),
            _finance_metric("Aguardando pagamento", S.pending, "clock_3", "amber"),
            _finance_metric("Vencido", S.overdue, "triangle_alert", "red"),
            _finance_metric("Confirmado, não disponível", S.confirmed, "circle_check", "blue"),
            columns=rx.breakpoints(initial="1", sm="2", xl="4"),
            gap="1rem", width="100%", class_name="vitta-finance-summary",
        ),
        rx.cond(S.error != "", rx.callout(S.error, color_scheme="red", role="alert")),
        rx.cond(S.success != "", rx.callout(S.success, color_scheme="teal", role="status")),
        rx.vstack(
            section_panel(
                rx.vstack(
                    rx.flex(
                        rx.box(rx.icon("filter", size=19), class_name="vitta-finance-filter-icon"),
                        rx.vstack(
                            rx.heading("Filtros de cobrança", size="4"),
                            rx.text("Localize cobranças por paciente, situação ou período.", size="2", color="var(--vitta-text-muted)"),
                            spacing="0", align="start",
                        ),
                        align="center", gap="1rem", width="100%",
                    ),
                    rx.form(rx.grid(
                        field("Paciente", rx.box(
                            rx.icon("search", size=17, aria_hidden="true"),
                            rx.input(
                                name="query", default_value=S.query,
                                placeholder="Pesquisar por nome",
                                aria_label="Pesquisar paciente",
                                class_name="vitta-finance-search-input",
                            ),
                            class_name="vitta-finance-search",
                        )),
                        field("Situação", status_select()),
                        field("Período", rx.flex(
                            rx.input(name="start", type="date", default_value=S.start,
                                     required=True, aria_label="Início do período"),
                            rx.text("até", size="2", color="var(--vitta-text-muted)"),
                            rx.input(name="end", type="date", default_value=S.end,
                                     required=True, aria_label="Fim do período"),
                        align="center", gap=".5rem", width="100%",
                            class_name="vitta-finance-date-range",
                        )),
                        rx.button(
                            rx.icon("filter", size=16, aria_hidden="true"),
                            "Aplicar filtros", type="submit", variant="outline",
                            color_scheme="teal", disabled=S.busy,
                            class_name="vitta-finance-filter-submit",
                        ),
                        columns=rx.breakpoints(
                            initial="1", sm="2",
                            xl="minmax(0, 1.3fr) minmax(0, 1fr) minmax(20rem, 1.6fr) auto",
                        ),
                    column_gap="1.5rem", row_gap=".75rem", align="end", width="100%",
                        class_name="vitta-finance-filters-form",
                    ), on_submit=S.filter, width="100%"),
                    rx.text(
                        "Recebido por data de recebimento; demais valores e listagem por vencimento. Valores brutos em reais.",
                        size="1",
                        class_name="vitta-sr-only",
                        id="finance-filter-context",
                    ),
                    spacing="3", width="100%", align="stretch",
                ),
                padding=".75rem 1.25rem .4rem",
                class_name="vitta-finance-filters",
            ),
            section_panel(
                rx.flex(
                    rx.box(
                        rx.icon("file_text", size=22, aria_hidden="true"),
                        class_name="vitta-finance-issue-icon",
                        aria_hidden="true",
                    ),
                    rx.vstack(
                        rx.heading("Emitir cobrança", size="4"),
                        rx.text(
                            "Escolha uma consulta existente. A pesquisa por paciente acima também limita estas opções.",
                            size="2",
                        ),
                        rx.form(rx.grid(
                            field("Consulta", rx.select(S.candidates, name="consultation", placeholder="Selecione a consulta", required=True)),
                            field("Valor em reais", rx.input(name="value", placeholder="0,00", required=True, aria_label="Valor da cobrança em reais")),
                            field("Vencimento", rx.input(type="date", name="due", required=True, aria_label="Vencimento da cobrança")),
                            field("Forma de pagamento", rx.select(["PIX", "BOLETO"], name="method", default_value="PIX", required=True)),
                            rx.button(
                                rx.icon("send", size=16, aria_hidden="true"),
                                "Emitir no Sandbox", type="submit",
                                disabled=S.busy | (S.candidates.length() == 0),
                                class_name="vitta-finance-issue-submit",
                            ),
                            columns=rx.breakpoints(
                                initial="1", sm="2",
                                xl="minmax(0, 1.25fr) minmax(8rem, 1fr) minmax(8rem, 1fr) minmax(0, 1.1fr) auto",
                            ),
                        column_gap="1.5rem", row_gap=".75rem", align="end", width="100%",
                            class_name="vitta-finance-issue-form",
                        ), on_submit=S.issue, width="100%"),
                        spacing="1", width="100%", min_width="0",
                        class_name="vitta-finance-issue-body",
                    ),
                    align="start", gap="1.125rem", width="100%",
                    class_name="vitta-finance-issue-layout",
                ),
                padding=".75rem .875rem .875rem",
                class_name="vitta-finance-issue",
                style={"background": "linear-gradient(110deg, #ffffff 0%, #effaf8 100%)"},
            ),
            section_panel(rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon("list", size=20, aria_hidden="true"),
                        class_name="vitta-finance-charge-icon",
                        aria_hidden="true",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.heading("Cobranças", size="3"),
                            rx.text(S.total.to_string(), " no período", size="1"),
                            align="center", gap=".5rem", flex_wrap="wrap",
                        ),
                        rx.text(
                            "Lista de cobranças conforme os filtros aplicados.",
                            size="1", color="var(--vitta-text-muted)",
                        ),
                        spacing="0", align="start", min_width="0",
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.icon("refresh_cw", size=16, aria_hidden="true"),
                        "Atualizar", on_click=S.load, disabled=S.busy,
                        variant="outline", color_scheme="teal",
                        class_name="vitta-finance-charge-refresh",
                    ),
                align="center", gap="1rem", flex_wrap="wrap", width="100%",
                    class_name="vitta-finance-charge-heading",
                ),
                rx.cond(
                    S.busy,
                    rx.center(rx.spinner(), min_height="7rem", width="100%", role="status"),
                    rx.vstack(
                        rx.box(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.table.column_header_cell("Paciente", scope="col"),
                                        rx.table.column_header_cell("Consulta", scope="col"),
                                        rx.table.column_header_cell("Valor", scope="col"),
                                        rx.table.column_header_cell("Vencimento", scope="col"),
                                        rx.table.column_header_cell("Situação", scope="col"),
                                        rx.table.column_header_cell("Ações", scope="col", justify="end"),
                                    ),
                                ),
                                rx.table.body(rx.foreach(S.rows, charge_row)),
                                width="100%", aria_label="Cobranças do período",
                                class_name="vitta-finance-charge-table",
                            ),
                            class_name="vitta-finance-charge-table-scroll",
                        ),
                        rx.cond(
                            S.rows.length() == 0,
                            _finance_charge_empty_state(),
                            rx.fragment(),
                        ),
                        spacing="0", width="100%", align="stretch",
                    ),
                ),
                rx.cond(
                    S.total > 20,
                    rx.hstack(
                        rx.button("Anterior", on_click=S.change_page(-1), disabled=S.busy | (S.page <= 1)),
                        rx.text("Página ", S.page.to_string()),
                        rx.button("Próxima", on_click=S.change_page(1), disabled=S.busy | (S.page * 20 >= S.total)),
                    ),
                    rx.fragment(),
                ),
                width="100%", align="stretch", spacing="3"),
                padding=".75rem 1.25rem 1rem", class_name="vitta-finance-charges"),
            section_panel(
                rx.flex(
                    rx.hstack(
                        rx.box(
                            rx.icon("chart_no_axes_column_increasing", size=22),
                            class_name="vitta-finance-evolution-icon",
                            aria_hidden="true",
                        ),
                        rx.vstack(
                            rx.heading("Evolução dos recebimentos", size="4"),
                            rx.text(
                                "Acompanhe os valores recebidos no período selecionado.",
                                size="2", color="var(--vitta-text-muted)",
                            ),
                            spacing="1", align="start", min_width="0",
                        ),
                    align="center", gap="1rem", min_width="0",
                        class_name="vitta-finance-evolution-copy",
                    ),
                    rx.cond(
                        S.evolution.length() == 0,
                        rx.hstack(
                            rx.icon(
                                "chart_no_axes_column_increasing", size=34,
                                color="var(--vitta-primary)", aria_hidden="true",
                            ),
                            rx.vstack(
                                rx.text("Sem recebimentos no período", font_weight="700"),
                                rx.text(
                                    "Emita cobranças e acompanhe os recebimentos aqui.",
                                    size="2", color="var(--vitta-text-muted)",
                                ),
                                spacing="1", align="start", min_width="0",
                            ),
                        align="center", gap="1.25rem", min_width="0",
                            role="status", aria_live="polite",
                            class_name="vitta-finance-evolution-empty",
                        ),
                        rx.vstack(
                            rx.foreach(S.evolution, _evolution_row),
                            spacing="2", align="stretch", width="100%", role="list",
                            aria_label="Recebimentos por dia, valores em reais",
                        ),
                    ),
                align="center", justify="between", gap="1.5rem", width="100%",
                    direction=rx.breakpoints(initial="column", xl="row"),
                    class_name="vitta-finance-evolution-layout",
                ),
                padding=".75rem 1.25rem", class_name="vitta-finance-evolution",
            ),
            spacing="4", width="100%", class_name="vitta-finance-panels",
        ),
        section_panel(operations_panel()),
        rx.dialog.root(rx.dialog.content(rx.vstack(
            rx.dialog.title("Detalhes da cobrança"), rx.dialog.description(S.selected_name),
            rx.text(S.selected_info, overflow_wrap="anywhere"),
            rx.cond(S.selected_url != "", rx.link("Abrir pagamento no Asaas", href=S.selected_url, is_external=True)),
            rx.flex(rx.button("Consultar situação", on_click=S.reconcile_selected, disabled=S.busy),
                    rx.button("Atualizar cliente", on_click=S.sync_customer, disabled=S.busy, variant="outline"),
                    rx.button("Consultar Pix", on_click=S.get_pix, disabled=S.busy),
                    rx.button("Cancelar cobrança", on_click=S.request_operation("CANCEL"), disabled=S.busy, variant="outline"),
                    rx.cond(AuthState.current_role == "ADMINISTRADOR", rx.button("Solicitar estorno Pix", on_click=S.request_operation("REFUND"), disabled=S.busy, variant="outline")), gap=".5rem", flex_wrap="wrap"),
            rx.cond(S.pix_payload != "", rx.vstack(rx.text("Pix copia e cola"), rx.text(S.pix_payload, overflow_wrap="anywhere"), rx.button("Copiar código Pix", on_click=rx.set_clipboard(S.pix_payload)))),
            rx.heading("Histórico", size="3"),
            rx.foreach(S.history, lambda row: rx.box(rx.text(row["status"], " · ", row["when"], size="2"), rx.text(row["source"], " · ", row["actor"], size="1"), rx.text(row["reason"], size="2"))),
            rx.dialog.close(rx.button("Fechar", variant="outline")), align="stretch", spacing="3"), max_width="42rem"), open=S.detail_open, on_open_change=S.close_detail),
        rx.alert_dialog.root(rx.alert_dialog.content(
            rx.alert_dialog.title("Confirmar operação financeira"),
            rx.alert_dialog.description("A ação será solicitada ao Asaas Sandbox para a cobrança selecionada. Confira paciente e valor antes de confirmar."),
            rx.text(S.selected_name), rx.text(S.selected_info),
            rx.form(rx.vstack(field("Motivo (sem informações clínicas)", rx.input(name="reason", required=True, min_length=3, max_length=240, aria_label="Motivo da operação financeira")),
                    rx.hstack(rx.alert_dialog.cancel(rx.button("Voltar", variant="outline", disabled=S.busy)), rx.button("Confirmar operação", type="submit", disabled=S.busy)), spacing="3"), on_submit=S.confirm_operation),
        ), open=S.confirmation_open, on_open_change=S.close_confirmation),
        align="stretch", spacing="3", width="100%",
        class_name="vitta-finance-workspace",
    )
