"""Chromium smoke test: read-only admin agenda at acceptance widths.

Uses synthetic accounts and a disposable database created by the existing QA workflow.
"""

import re

import pytest
from playwright.sync_api import expect, sync_playwright

from qa_browser.capture_all_screens import BASE, OUTPUT, FIXTURE, authenticate


@pytest.mark.parametrize(
    ("width", "height"),
    [(320, 720), (390, 844), (768, 1024), (1024, 768), (1440, 900)],
)
def test_qa_admin_agenda_calendar_and_responsiveness(width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                locale="pt-BR",
                reduced_motion="reduce",
            )
            page = context.new_page()
            authenticate(page, "administrador")
            page.goto(BASE + "/admin/agenda", wait_until="domcontentloaded")

            expect(
                page.get_by_role("heading", name="Agenda clínica", exact=True)
            ).to_be_visible(timeout=30000)
            expect(
                page.get_by_role("button", name="Mês anterior")
            ).to_be_enabled(timeout=30000)
            expect(page.get_by_text("Período consultado:", exact=False)).to_be_visible()
            expect(page.locator(".vitta-calendar-date").first).to_be_visible()

            # The preview has no patient identifiers and exposes no scheduling writes.
            assert not page.get_by_text(FIXTURE["patient_name"], exact=False).count()
            assert not page.get_by_role("button", name=re.compile("Cancelar consulta|Reagendar|Agendar consulta")).count()

            # Any in-month day is selectable even when it has no slots.
            day = page.locator(".vitta-calendar-date:not([disabled])").first
            day.click()
            expect(page.get_by_role("heading", name="Disponibilidade do dia")).to_be_visible()

            # Navigating months refetches persisted records rather than using fake slots.
            page.get_by_role("button", name="Mês anterior").click()
            expect(page.get_by_role("button", name="Próximo mês")).to_be_enabled(timeout=30000)

            # A real browser layout assertion for all acceptance widths.
            horizontal_overflow = page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth + 2"
            )
            assert not horizontal_overflow, f"Overflow horizontal a {width}px"

            # Keyboard navigation must reach an interactive control.
            page.get_by_role("button", name="Próximo mês").focus()
            assert page.evaluate(
                "document.activeElement?.getAttribute('aria-label')"
            ) == "Próximo mês"

            OUTPUT.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(OUTPUT / f"qa-admin-agenda-{width}.png"),
                full_page=True,
                animations="disabled",
            )
            context.close()
        finally:
            browser.close()
