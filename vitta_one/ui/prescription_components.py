"""Read-only prescription document surface prepared for browser printing."""

import reflex as rx

from vitta_one.clinical_prescription.state import PrintPrescriptionState
from vitta_one.ui.components import brand_logo, loading_surface

NO_DIGITAL_SIGNATURE_NOTICE = "Documento sem assinatura digital nesta etapa."


def _print_item(item) -> rx.Component:
    return rx.box(
        rx.text(
            item["medication_or_item"],
            font_weight="850",
            font_size="1rem",
            overflow_wrap="anywhere",
        ),
        rx.text(
            item["instructions"],
            font_size="0.94rem",
            line_height="1.65",
            white_space="pre-wrap",
            overflow_wrap="anywhere",
            margin_top="0.3rem",
        ),
        rx.cond(
            item["notes"] != "",
            rx.text(
                item["notes"],
                font_size="0.82rem",
                color="var(--vitta-text-muted)",
                line_height="1.55",
                white_space="pre-wrap",
                overflow_wrap="anywhere",
                margin_top="0.35rem",
            ),
            rx.fragment(),
        ),
        class_name="vitta-print-prescription-item",
        role="listitem",
    )


def _print_document() -> rx.Component:
    return rx.box(
        rx.flex(
            brand_logo(width="9.5rem"),
            rx.box(
                rx.text("PRESCRIÇÃO", class_name="vitta-print-kicker"),
                rx.text(
                    "Documento clínico",
                    font_size="0.82rem",
                    color="var(--vitta-text-muted)",
                    margin_top="0.2rem",
                ),
                text_align=rx.breakpoints(initial="left", sm="right"),
            ),
            direction=rx.breakpoints(initial="column", sm="row"),
            justify="between",
            align=rx.breakpoints(initial="start", sm="center"),
            gap="1rem",
            width="100%",
        ),
        rx.box(class_name="vitta-print-rule"),
        rx.grid(
            rx.box(
                rx.text("Paciente", class_name="vitta-print-label"),
                rx.text(PrintPrescriptionState.patient_name, font_weight="800", margin_top="0.2rem"),
            ),
            rx.box(
                rx.text("Consulta", class_name="vitta-print-label"),
                rx.text(
                    PrintPrescriptionState.scheduled_at,
                    class_name="vitta-tabular",
                    margin_top="0.2rem",
                ),
            ),
            rx.box(
                rx.text("Profissional", class_name="vitta-print-label"),
                rx.text(PrintPrescriptionState.professional_name, font_weight="750", margin_top="0.2rem"),
                rx.text(
                    PrintPrescriptionState.registration_identifier,
                    font_size="0.8rem",
                    color="var(--vitta-text-muted)",
                    margin_top="0.15rem",
                ),
            ),
            columns=rx.breakpoints(initial="1", md="3"),
            gap="1rem",
            width="100%",
            margin_top="1.2rem",
        ),
        rx.box(
            rx.text("Itens prescritos", font_weight="850", font_size="1.05rem"),
            rx.vstack(
                rx.foreach(PrintPrescriptionState.items, _print_item),
                spacing="3",
                align="stretch",
                width="100%",
                role="list",
                margin_top="0.75rem",
            ),
            margin_top="1.5rem",
        ),
        rx.cond(
            PrintPrescriptionState.general_notes != "",
            rx.box(
                rx.text("Observações gerais", class_name="vitta-print-label"),
                rx.text(
                    PrintPrescriptionState.general_notes,
                    white_space="pre-wrap",
                    overflow_wrap="anywhere",
                    line_height="1.6",
                    margin_top="0.35rem",
                ),
                class_name="vitta-print-notes",
                margin_top="1.25rem",
            ),
            rx.fragment(),
        ),
        rx.box(
            rx.icon("shield_alert", size=18),
            rx.text(
                NO_DIGITAL_SIGNATURE_NOTICE,
                font_weight="750",
                size="2",
            ),
            class_name="vitta-print-signature-notice",
            margin_top="1.6rem",
        ),
        rx.text(
            "Vitta-One · Prescrição clínica",
            font_size="0.72rem",
            color="var(--vitta-text-subtle)",
            margin_top="1.75rem",
        ),
        class_name="vitta-print-document",
    )


def prescription_print_page() -> rx.Component:
    return rx.box(
        rx.cond(
            PrintPrescriptionState.is_loading,
            loading_surface("Abrindo Prescrição…"),
            rx.cond(
                PrintPrescriptionState.loaded,
                rx.box(
                    rx.flex(
                        rx.button(
                            rx.hstack(
                                rx.icon("arrow_left", size=16),
                                rx.text("Voltar ao atendimento"),
                                spacing="2",
                                align="center",
                            ),
                            type="button",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=rx.redirect("/medico"),
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("printer", size=16),
                                rx.text("Imprimir"),
                                spacing="2",
                                align="center",
                            ),
                            type="button",
                            color_scheme="teal",
                            high_contrast=True,
                            on_click=rx.call_script("window.print()"),
                        ),
                        justify="between",
                        align="center",
                        gap="0.75rem",
                        width="100%",
                        class_name="vitta-print-controls",
                    ),
                    _print_document(),
                    width="min(100%, 58rem)",
                    margin="0 auto",
                    padding=rx.breakpoints(initial="1rem", sm="1.5rem"),
                ),
                rx.center(
                    rx.box(
                        brand_logo(width="8rem"),
                        rx.heading("Prescrição indisponível", size="6", margin_top="1.2rem"),
                        rx.text(
                            PrintPrescriptionState.error_message,
                            color="var(--vitta-text-muted)",
                            line_height="1.6",
                            margin_top="0.5rem",
                        ),
                        rx.button(
                            "Voltar ao atendimento",
                            type="button",
                            variant="outline",
                            color_scheme="teal",
                            on_click=rx.redirect("/medico"),
                            margin_top="1rem",
                        ),
                        class_name="vitta-print-error-card",
                    ),
                    min_height="100dvh",
                    padding="1rem",
                ),
            ),
        ),
        min_height="100dvh",
        background="var(--vitta-canvas)",
        class_name="vitta-print-page",
    )
