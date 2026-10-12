"""Real Chromium acceptance tests for protected prescription routes and physician UI.

No mocking of Reflex State or backend. Every browser context starts with a fresh
session. These tests run against a *disposable* real Reflex + PostgreSQL instance.
"""
import json
import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, sync_playwright


BASE = os.getenv("QA_BASE_URL", "http://127.0.0.1:3000")
FIXTURE = json.loads(Path("qa-artifacts/fixture.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        instance = playwright.chromium.launch(headless=True)
        yield instance
        instance.close()


@pytest.fixture()
def page(browser, request):
    context = browser.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    screen = context.new_page()
    yield screen
    if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
        path = Path("qa-artifacts") / (request.node.name[:90] + ".png")
        screen.screenshot(path=str(path), full_page=True)
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


def login(page: Page, email: str) -> None:
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.locator("#login-email").fill(email)
    page.locator("#login-password").fill(os.environ["VITTA_ONE_QA_PASSWORD"])
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(re.compile(r"/medico/?$"), timeout=30000)
    expect(page.get_by_role("heading", name=re.compile("Médico|Atendimento|Fila", re.I)).first).to_be_visible(timeout=30000)




def overflowing_elements(page: Page):
    return page.evaluate("""() => {
        const width = window.innerWidth;
        return [...document.querySelectorAll('body *')]
            .map((el) => {
                const rect = el.getBoundingClientRect();
                return {
                    element: el.tagName.toLowerCase(),
                    className: String(el.className).slice(0, 100),
                    text: (el.textContent || '').trim().slice(0, 48),
                    left: Math.round(rect.left),
                    right: Math.round(rect.right),
                    width: Math.round(rect.width),
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth
                };
            })
            .filter(el => el.right > width + 2 && el.width > 2)
            .sort((a, b) => b.right - a.right)
            .slice(0, 12);
    }""")

def print_url() -> str:
    return f"{BASE}/medico/prescricao/{FIXTURE['prescription_id']}"


def test_unauthenticated_deep_link_never_renders_prescription(page: Page) -> None:
    """15.10: new browser context, direct navigation, no authentication."""
    page.goto(print_url(), wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/login/?$"), timeout=30000)
    expect(page.get_by_text(FIXTURE["patient_name"])).to_have_count(0)
    assert "Medicamento Fictício QA" not in page.locator("body").inner_text()


def test_another_doctor_cannot_open_print_route(page: Page) -> None:
    """15.9: authenticated wrong doctor, direct URL + reload."""
    login(page, FIXTURE["doctor_b_email"])
    page.goto(print_url(), wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/acesso-negado/?$"), timeout=30000)
    expect(page.get_by_text(FIXTURE["patient_name"])).to_have_count(0)
    assert "Medicamento Fictício QA" not in page.locator("body").inner_text()
    page.reload()
    expect(page.get_by_text(FIXTURE["patient_name"])).to_have_count(0)


def test_author_sees_print_document_and_signature_notice(page: Page) -> None:
    """Positive control: genuine authorized user sees expected synthetic content."""
    login(page, FIXTURE["doctor_a_email"])
    page.goto(print_url(), wait_until="domcontentloaded")
    expect(page.get_by_text(FIXTURE["patient_name"])).to_be_visible(timeout=30000)
    expect(page.get_by_text("Medicamento Fictício QA")).to_be_visible()
    expect(page.get_by_text("Documento sem assinatura digital nesta etapa.")).to_be_visible()
    expect(page.get_by_role("button", name="Imprimir")).to_be_visible()


def test_doctor_prescription_dialog_keyboard_focus_and_responsive_layout(page: Page) -> None:
    """10.18, 10.20, 11.8 and 13.8: actual rendered dialog, focus, motion, widths."""
    login(page, FIXTURE["doctor_a_email"])
    for width, height in ((320, 640), (375, 667), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        page.emulate_media(reduced_motion="reduce")
        expect(page.get_by_role("button", name="Nova prescrição")).to_be_visible(timeout=30000)
        trigger = page.get_by_role("button", name="Nova prescrição")
        trigger.focus()
        trigger.press("Enter")
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible(timeout=15000)
        first = dialog.locator("#new-prescription-medication")
        expect(first).to_be_focused(timeout=10000)
        assert first.get_attribute("aria-describedby") == "new-prescription-medication-help"
        first.press("Tab")
        expect(dialog.locator("#new-prescription-instructions")).to_be_focused(timeout=10000)
        dialog.locator("#new-prescription-instructions").press("Shift+Tab")
        expect(first).to_be_focused(timeout=10000)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 2"), overflowing_elements(page)
        assert page.evaluate(
            "getComputedStyle(document.documentElement).getPropertyValue('--vitta-focus').trim() != ''"
        )
        assert page.evaluate(
            "getComputedStyle(document.querySelector('#new-prescription-medication')).animationDuration"
        ) in ("0s", "0.00001s", "1e-05s", "0.01ms")
        first.press("Escape")
        expect(dialog).to_have_count(0, timeout=15000)
        expect(trigger).to_be_focused(timeout=10000)



def test_other_prescription_dialogs_start_with_safe_focus(page: Page) -> None:
    """11.8: inspect initial focus for add/edit, notes, remove, delete dialogs."""
    login(page, FIXTURE["doctor_a_email"])
    cases = [
        ("Adicionar item", "#prescription-item-medication"),
        ("Editar", "#prescription-item-medication"),
        ("Editar observações gerais", "#prescription-general-notes"),
        ("Remover", "button:has-text('Manter item')"),
        ("Excluir prescrição", "button:has-text('Manter prescrição')"),
    ]
    for label, target in cases:
        trigger = page.get_by_role("button", name=label, exact=True).first
        expect(trigger).to_be_enabled(timeout=15000)
        trigger.focus()
        trigger.press("Enter")
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible(timeout=15000)
        expect(dialog.locator(target)).to_be_focused(timeout=15000)
        dialog.locator(target).press("Escape")
        expect(dialog).to_have_count(0, timeout=15000)


def test_completed_history_and_prescriptions_fit_narrow_viewports(page: Page) -> None:
    """13.8: render a nonempty history and expand an actual prescription disclosure."""
    login(page, FIXTURE["doctor_a_email"])
    expect(page.get_by_role("heading", name="Histórico clínico")).to_be_visible(timeout=15000)
    disclosure = page.locator(".vitta-prescription-history-disclosure").first
    expect(disclosure).to_be_visible(timeout=15000)
    for width, height in ((320, 640), (375, 667), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        disclosure.locator("summary").click()
        expect(disclosure.get_by_text("Histórico Fictício QA")).to_be_visible(timeout=15000)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), f"horizontal overflow detected at {width}px with history open: {overflowing_elements(page)}"
        disclosure.locator("summary").click()
