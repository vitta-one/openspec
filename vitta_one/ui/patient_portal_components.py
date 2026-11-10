"""Patient-owned documents and financial account surfaces."""

import reflex as rx

from vitta_one.patient_portal.state import PatientPortalState
from vitta_one.ui.components import empty_state, section_panel


def _document(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.box(rx.icon("file_text", size=19), class_name="vitta-list-icon"),
                rx.box(
                    rx.text(row["title"], font_weight="800", color="var(--vitta-text)"),
                    rx.text(row["category"] + " · " + row["date"] + " · " + row["size"], size="2", color="var(--vitta-text-muted)"),
                ), gap="3", align="center",
            ),
            rx.button("Abrir", size="2", variant="outline", on_click=PatientPortalState.open_attachment(row["id"]), aria_label="Abrir " + row["title"]),
            justify="between", align="center", gap="3", width="100%", flex_wrap="wrap",
        ),
        class_name="vitta-list-row",
    )


def _prescription(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(rx.text("Prescrição", font_weight="800"), rx.text(row["date"], size="2", color="var(--vitta-text-muted)")),
            rx.hstack(
                rx.badge(row["status"], variant="soft", color_scheme=rx.cond(row["status"] == "SIGNED", "teal", "amber")),
                rx.cond(row["can_open"], rx.button("Abrir assinada", size="2", variant="outline", on_click=PatientPortalState.open_signed_prescription(row["id"])), rx.fragment()),
                gap="2", align="center",
            ),
            justify="between", align="center", gap="3", width="100%", flex_wrap="wrap",
        ),
        class_name="vitta-list-row",
    )


def patient_documents_panel() -> rx.Component:
    return section_panel(
        rx.box(rx.heading("Meus documentos", size="5"), rx.text("Exames liberados e prescrições em assinatura.", size="2", color="var(--vitta-text-muted)")),
        rx.cond(
            PatientPortalState.has_documents,
            rx.vstack(
                rx.foreach(PatientPortalState.document_rows, _document),
                rx.foreach(PatientPortalState.prescription_rows, _prescription),
                width="100%", gap="3", margin_top="1rem",
            ),
            empty_state("file_text", "Nenhum documento disponível", "Quando a equipe liberar um exame ou uma prescrição assinada, ele aparecerá aqui."),
        ),
    )


def _financial(row) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.text("Conta #" + row["id"].to(str), font_weight="800"),
                rx.text("Vencimento " + row["due_date"], size="2", color="var(--vitta-text-muted)"),
            ),
            rx.badge(row["status"], variant="soft", color_scheme="teal"),
            justify="between", gap="3", width="100%",
        ),
        rx.hstack(rx.text("Total: " + row["total"], size="2"), rx.text("Saldo: " + row["balance"], size="2", font_weight="700"), gap="4", margin_top="0.7rem", flex_wrap="wrap"),
        rx.cond(row["invoice_url"] != "", rx.link("Abrir página de pagamento", href=row["invoice_url"], target="_blank", rel="noopener noreferrer", class_name="vitta-context-link", display="inline-block", margin_top="0.8rem"), rx.fragment()),
        class_name="vitta-list-row",
    )


def patient_financial_panel() -> rx.Component:
    return section_panel(
        rx.box(rx.heading("Financeiro", size="5"), rx.text("Contas e cobranças vinculadas ao seu cadastro.", size="2", color="var(--vitta-text-muted)")),
        rx.cond(
            PatientPortalState.has_financial_accounts,
            rx.vstack(rx.foreach(PatientPortalState.financial_rows, _financial), width="100%", gap="3", margin_top="1rem"),
            empty_state("wallet", "Nenhuma conta em aberto", "Sua situação financeira aparecerá aqui quando houver uma conta emitida."),
        ),
    )
