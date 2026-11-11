"""Financial workspace using the existing Vitta-One shell and visual tokens."""
import reflex as rx

from vitta_one.auth.state import AuthState
from vitta_one.ui.components import page_header, section_panel
from .state import FinancialState as S
from .application import LABELS
from vitta_one.notifications.operations import operations_panel


def field(label: str, control: rx.Component):
    return rx.vstack(rx.text(label, size="2", font_weight="600"), control, spacing="1", align="stretch", width="100%")


def status_select():
    return rx.select.root(rx.select.trigger(placeholder="Todas as situações"), rx.select.content(
        rx.select.item("Todas as situações", value="ALL"),
        *[rx.select.item(label, value=code) for code, label in LABELS.items()]), name="status", default_value="ALL")


def charge_row(row):
    return rx.flex(
        rx.vstack(rx.text(row["patient"], font_weight="650"), rx.text("Consulta ", row["consultation"], size="2"), spacing="1"),
        rx.text(row["value"], font_weight="650"), rx.text(row["due"]), rx.text(row["method"]),
        rx.text(row["status"], size="2"),
        rx.button("Ver detalhes", on_click=S.show(row["id"]), variant="outline", disabled=S.busy),
        direction={"initial": "column", "md": "row"}, gap="3", align={"initial": "start", "md": "center"},
        justify="between", padding="1rem", border_bottom="1px solid var(--vitta-border)", width="100%",
    )


def finance_content():
    return rx.vstack(
        page_header("Vitta-One", "Financeiro", "Cobranças e recebimentos · Asaas Sandbox"),
        rx.cond(S.error != "", rx.callout(S.error, color_scheme="red", role="alert")),
        rx.cond(S.success != "", rx.callout(S.success, color_scheme="teal", role="status")),
        rx.form(rx.flex(
            field("Paciente", rx.input(name="query", default_value=S.query, placeholder="Pesquisar por nome", aria_label="Pesquisar paciente")),
            field("Situação", status_select()),
            field("De", rx.input(name="start", type="date", default_value=S.start, required=True, aria_label="Início do período")),
            field("Até", rx.input(name="end", type="date", default_value=S.end, required=True, aria_label="Fim do período")),
            rx.button("Aplicar filtros", type="submit", disabled=S.busy),
            direction={"initial": "column", "md": "row"}, gap="3", align="end", width="100%"), on_submit=S.filter, width="100%"),
        rx.text("Recebido por data de recebimento; demais valores e listagem por vencimento. Valores brutos em reais.", size="2"),
        rx.grid(*[section_panel(rx.vstack(rx.text(title, size="2"), rx.text(value, size="5", font_weight="700")))
                  for title, value in [("Recebido", S.received), ("Aguardando pagamento", S.pending), ("Vencido", S.overdue), ("Confirmado, não disponível", S.confirmed)]],
                columns={"initial": "1", "sm": "2", "lg": "4"}, gap="3", width="100%"),
        section_panel(rx.vstack(
            rx.heading("Emitir cobrança", size="4"),
            rx.text("Escolha uma consulta existente. A pesquisa por paciente acima também limita estas opções.", size="2"),
            rx.form(rx.flex(
                field("Consulta", rx.select(S.candidates, name="consultation", placeholder="Selecione a consulta", required=True)),
                field("Valor em reais", rx.input(name="value", placeholder="0,00", required=True, aria_label="Valor da cobrança em reais")),
                field("Vencimento", rx.input(type="date", name="due", required=True, aria_label="Vencimento da cobrança")),
                field("Forma de pagamento", rx.select(["PIX", "BOLETO"], name="method", default_value="PIX", required=True)),
                rx.button("Emitir no Sandbox", type="submit", disabled=S.busy | (S.candidates.length() == 0)),
                direction={"initial": "column", "lg": "row"}, gap="3", align="end", width="100%"), on_submit=S.issue, width="100%"),
            spacing="3", width="100%")),
        section_panel(rx.vstack(
            rx.hstack(rx.heading("Cobranças", size="4"), rx.text(S.total.to_string(), " no período"), rx.spacer(), rx.button("Atualizar", on_click=S.load, disabled=S.busy), flex_wrap="wrap", width="100%"),
            rx.cond(S.busy, rx.spinner()),
            rx.cond(S.rows.length() == 0, rx.text("Nenhuma cobrança encontrada para os filtros."), rx.foreach(S.rows, charge_row)),
            rx.hstack(rx.button("Anterior", on_click=S.change_page(-1), disabled=S.busy | (S.page <= 1)),
                      rx.text("Página ", S.page.to_string()), rx.button("Próxima", on_click=S.change_page(1), disabled=S.busy | (S.page * 20 >= S.total))),
            width="100%", align="stretch", spacing="3")),
        section_panel(rx.vstack(rx.heading("Evolução dos recebimentos", size="4"),
            rx.cond(S.evolution.length() == 0, rx.text("Sem recebimentos no período."), rx.foreach(S.evolution,
                lambda row: rx.hstack(rx.text(row["day"]), rx.spacer(), rx.text(row["value"])))), width="100%")),
        section_panel(operations_panel()),
        rx.dialog.root(rx.dialog.content(rx.vstack(
            rx.dialog.title("Detalhes da cobrança"), rx.dialog.description(S.selected_name),
            rx.text(S.selected_info, overflow_wrap="anywhere"),
            rx.cond(S.selected_url != "", rx.link("Abrir pagamento no Asaas", href=S.selected_url, is_external=True)),
            rx.flex(rx.button("Consultar situação", on_click=S.reconcile_selected, disabled=S.busy),
                    rx.button("Atualizar cliente", on_click=S.sync_customer, disabled=S.busy, variant="outline"),
                    rx.button("Consultar Pix", on_click=S.get_pix, disabled=S.busy),
                    rx.button("Cancelar cobrança", on_click=S.request_operation("CANCEL"), disabled=S.busy, variant="outline"),
                    rx.cond(AuthState.current_role == "ADMINISTRADOR", rx.button("Solicitar estorno Pix", on_click=S.request_operation("REFUND"), disabled=S.busy, variant="outline")), gap="2", flex_wrap="wrap"),
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
        align="stretch", spacing="5", width="100%",
    )
