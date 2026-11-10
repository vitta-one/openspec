"""Task-oriented Financeiro surfaces."""

import reflex as rx

from vitta_one.finance.state import FinanceState
from vitta_one.ui.components import empty_state, field_label, section_panel


def _metric(label: str, value, hint: str) -> rx.Component:
    return rx.box(
        rx.text(label, size="2", color="var(--vitta-text-muted)", font_weight="700"),
        rx.text(value, font_size="1.45rem", font_weight="800", color="var(--vitta-text)", margin_top="0.3rem"),
        rx.text(hint, size="1", color="var(--vitta-text-subtle)", margin_top="0.2rem"),
        class_name="vitta-summary-tile",
    )


def finance_summary() -> rx.Component:
    return rx.grid(
        _metric("Em aberto", FinanceState.open_total, "Saldo de contas não canceladas"),
        _metric("Vencido", FinanceState.overdue_total, "Saldo com vencimento anterior a hoje"),
        _metric("Recebido", FinanceState.received_total, "Pagamentos conciliados"),
        columns=rx.breakpoints(initial="1", sm="3"), gap="3", width="100%",
    )


def finance_forms() -> rx.Component:
    service_form = rx.el.form(
        rx.vstack(
            rx.heading("Novo serviço", size="4"),
            rx.box(field_label("Nome", "finance-service-name"), rx.el.input(id="finance-service-name", name="name", required=True, max_length=160, class_name="vitta-input", margin_top="0.4rem"), width="100%"),
            rx.box(field_label("Descrição", "finance-service-description"), rx.el.textarea(id="finance-service-description", name="description", max_length=2000, class_name="vitta-textarea", margin_top="0.4rem"), width="100%"),
            rx.box(field_label("Preço", "finance-service-price"), rx.el.input(id="finance-service-price", name="price", required=True, input_mode="decimal", placeholder="150,00", class_name="vitta-input", margin_top="0.4rem"), width="100%"),
            rx.button("Cadastrar serviço", type="submit", color_scheme="teal", high_contrast=True, loading=FinanceState.is_submitting, min_height="2.75rem"),
            width="100%", align="stretch", gap="3",
        ),
        on_submit=FinanceState.create_service,
        reset_on_submit=False,
        width="100%",
    )
    account_form = rx.el.form(
        rx.vstack(
            rx.heading("Emitir conta", size="4"),
            rx.box(
                field_label("Paciente", "finance-account-patient"),
                rx.el.select(
                    rx.el.option("Selecione", value=""),
                    rx.foreach(FinanceState.patient_rows, lambda row: rx.el.option(row["name"], value=row["id"].to(str))),
                    id="finance-account-patient", name="patient_id", required=True,
                    class_name="vitta-select", margin_top="0.4rem",
                ), width="100%",
            ),
            rx.box(
                field_label("Serviço", "finance-account-service"),
                rx.el.select(
                    rx.el.option("Selecione", value=""),
                    rx.foreach(
                        FinanceState.service_rows,
                        lambda row: rx.cond(
                            row["active"],
                            rx.el.option(row["name"] + " · " + row["price"], value=row["id"].to(str)),
                            rx.fragment(),
                        ),
                    ),
                    id="finance-account-service", name="service_id", required=True,
                    class_name="vitta-select", margin_top="0.4rem",
                ), width="100%",
            ),
            rx.grid(
                rx.box(field_label("Quantidade", "finance-account-quantity"), rx.el.input(id="finance-account-quantity", name="quantity", type="number", min=1, max=100, default_value="1", required=True, class_name="vitta-input", margin_top="0.4rem")),
                rx.box(field_label("Vencimento", "finance-account-due"), rx.el.input(id="finance-account-due", name="due_date", type="date", required=True, class_name="vitta-input", margin_top="0.4rem")),
                columns=rx.breakpoints(initial="1", sm="2"), gap="3", width="100%",
            ),
            rx.button("Emitir conta", type="submit", color_scheme="teal", high_contrast=True, loading=FinanceState.is_submitting, disabled=~FinanceState.has_services, min_height="2.75rem"),
            width="100%", align="stretch", gap="3",
        ),
        on_submit=FinanceState.issue_account,
        reset_on_submit=False,
        width="100%",
    )
    return rx.grid(section_panel(service_form), section_panel(account_form), columns=rx.breakpoints(initial="1", lg="2"), gap="4", width="100%")


def _account_row(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(row["patient_name"], font_weight="800", color="var(--vitta-text)"),
                rx.text("Vence em " + row["due_date"], size="2", color="var(--vitta-text-muted)"),
            ),
            rx.badge(row["status"], variant="soft", color_scheme="teal"),
            justify="between", align="start", gap="3", width="100%",
        ),
        rx.grid(
            rx.box(rx.text("Total", size="1", color="var(--vitta-text-subtle)"), rx.text(row["total"], font_weight="700")),
            rx.box(rx.text("Pago", size="1", color="var(--vitta-text-subtle)"), rx.text(row["paid"], font_weight="700")),
            rx.box(rx.text("Saldo", size="1", color="var(--vitta-text-subtle)"), rx.text(row["balance"], font_weight="700")),
            columns="3", gap="3", margin_top="0.9rem", width="100%",
        ),
        rx.flex(
            rx.cond(
                row["charge_id"] == 0,
                rx.fragment(
                    rx.button("Gerar Pix", size="2", variant="soft", on_click=FinanceState.create_charge(row["id"], "PIX"), disabled=FinanceState.is_submitting),
                    rx.button("Gerar boleto", size="2", variant="outline", on_click=FinanceState.create_charge(row["id"], "BOLETO"), disabled=FinanceState.is_submitting),
                ),
                rx.fragment(
                    rx.badge("Asaas · " + row["charge_status"], variant="outline"),
                    rx.cond(row["invoice_url"] != "", rx.link("Abrir cobrança", href=row["invoice_url"], target="_blank", rel="noopener noreferrer", class_name="vitta-context-link"), rx.fragment()),
                    rx.cond(
                        row["charge_status"] == "RECONCILIATION_REQUIRED",
                        rx.button(
                            "Verificar no Asaas", size="2", variant="outline",
                            on_click=FinanceState.reconcile_charge(row["charge_id"]),
                            disabled=FinanceState.is_submitting,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        (row["charge_status"] == "PENDING") | (row["charge_status"] == "OVERDUE"),
                        rx.button(
                            "Cancelar", size="2", variant="ghost", color_scheme="red",
                            on_click=FinanceState.begin_cancel_charge(row["charge_id"], row["patient_name"]),
                            disabled=FinanceState.is_submitting,
                        ),
                        rx.fragment(),
                    ),
                ),
            ),
            gap="2", flex_wrap="wrap", align="center", margin_top="1rem",
        ),
        class_name="vitta-list-row",
    )


def finance_services() -> rx.Component:
    return section_panel(
        rx.heading("Catálogo de serviços", size="5"),
        rx.text(
            "Valores do catálogo são copiados para a conta no momento da emissão.",
            size="2", color="var(--vitta-text-muted)", margin_top="0.25rem",
        ),
        rx.cond(
            FinanceState.service_rows.length() > 0,
            rx.vstack(
                rx.foreach(
                    FinanceState.service_rows,
                    lambda row: rx.flex(
                        rx.box(
                            rx.text(row["name"], font_weight="750"),
                            rx.text(row["price"], size="2", color="var(--vitta-text-muted)"),
                        ),
                        rx.hstack(
                            rx.badge(
                                rx.cond(row["active"], "Ativo", "Inativo"),
                                color_scheme=rx.cond(row["active"], "green", "gray"),
                                variant="soft",
                            ),
                            rx.button(
                                rx.cond(row["active"], "Desativar", "Ativar"),
                                type="button", size="1", variant="outline",
                                color_scheme=rx.cond(row["active"], "gray", "teal"),
                                on_click=FinanceState.set_service_active(row["id"], ~row["active"]),
                                disabled=FinanceState.is_submitting,
                            ),
                            spacing="2",
                        ),
                        justify="between", align="center", gap="3", width="100%",
                        class_name="vitta-list-row",
                    ),
                ),
                width="100%", align="stretch", gap="2", margin_top="1rem",
            ),
            empty_state("briefcase_business", "Nenhum serviço cadastrado", "Cadastre o primeiro serviço para emitir contas."),
        ),
    )


def finance_accounts() -> rx.Component:
    return section_panel(
        rx.flex(
            rx.box(rx.heading("Contas e cobranças", size="5"), rx.text("Valores persistidos e conciliados por webhook.", size="2", color="var(--vitta-text-muted)")),
            rx.badge(FinanceState.asaas_status, variant="soft", color_scheme=rx.cond(FinanceState.asaas_status == "CONFIGURED", "teal", "amber")),
            justify="between", align="start", gap="3", width="100%", flex_wrap="wrap",
        ),
        rx.grid(
            rx.box(
                field_label("Buscar por paciente", "finance-account-query"),
                rx.input(
                    id="finance-account-query",
                    value=FinanceState.account_query,
                    on_change=FinanceState.update_account_query,
                    placeholder="Nome do paciente",
                    width="100%", margin_top="0.4rem",
                ),
            ),
            rx.box(
                field_label("Filtrar por status", "finance-account-status"),
                rx.select(
                    ["TODOS", "OPEN", "PARTIALLY_PAID", "PAID", "PENDING", "OVERDUE", "RECONCILIATION_REQUIRED"],
                    id="finance-account-status",
                    value=FinanceState.account_status_filter,
                    on_change=FinanceState.update_account_status_filter,
                    width="100%", margin_top="0.4rem",
                ),
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            gap="3", width="100%", margin_top="1rem",
        ),
        rx.cond(
            FinanceState.has_accounts,
            rx.cond(
                FinanceState.filtered_account_rows.length() > 0,
                rx.vstack(rx.foreach(FinanceState.filtered_account_rows, _account_row), width="100%", gap="3", margin_top="1rem"),
                empty_state("search", "Nenhuma conta encontrada", "Ajuste a busca ou o filtro de status."),
            ),
            empty_state("receipt", "Nenhuma conta emitida", "Cadastre um serviço e emita a primeira conta do paciente."),
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.content(
                rx.alert_dialog.title("Cancelar cobrança?"),
                rx.alert_dialog.description(
                    "A cobrança hospedada no Asaas será cancelada. A conta clínica e seu histórico permanecerão registrados.",
                    margin_top="0.4rem",
                ),
                rx.text(
                    FinanceState.cancel_charge_patient_name,
                    font_weight="750", margin_top="0.75rem",
                ),
                rx.flex(
                    rx.button(
                        "Voltar", type="button", variant="outline", color_scheme="gray",
                        on_click=FinanceState.set_cancel_charge_dialog_open(False),
                        disabled=FinanceState.is_submitting,
                    ),
                    rx.button(
                        "Cancelar cobrança", type="button", color_scheme="red", high_contrast=True,
                        on_click=FinanceState.cancel_charge,
                        loading=FinanceState.is_submitting,
                        disabled=FinanceState.is_submitting,
                    ),
                    direction=rx.breakpoints(initial="column-reverse", sm="row"),
                    justify="end", gap="0.65rem", width="100%", margin_top="1.25rem",
                ),
                class_name="vitta-dialog-content", max_width="34rem",
            ),
            open=FinanceState.cancel_charge_dialog_open,
            on_open_change=FinanceState.set_cancel_charge_dialog_open,
        ),
    )


def finance_workspace() -> rx.Component:
    return rx.vstack(finance_summary(), finance_forms(), finance_services(), finance_accounts(), width="100%", align="stretch", gap="5")

