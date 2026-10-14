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
    page.screenshot(path="qa-artifacts/documento-imprimivel.png", full_page=True)


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
        page.screenshot(path=f"qa-artifacts/dialogo-nova-prescricao-{width}px.png", full_page=True)
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
        page.screenshot(path=f"qa-artifacts/historico-{width}px.png", full_page=True)
        disclosure.locator("summary").click()


def login_as_admin(page: Page) -> None:
    """Use only the CI disposable database's synthetic Administrator."""
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.locator("#login-email").fill(FIXTURE["admin_email"])
    page.locator("#login-password").fill(os.environ["VITTA_ONE_QA_PASSWORD"])
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(re.compile(r"/admin/?$"), timeout=30000)
    expect(page.get_by_role("heading", name="Especialidades", exact=True)).to_be_visible(timeout=30000)


def test_admin_dashboard_is_compact_and_routes_to_complete_directory(page: Page) -> None:
    login_as_admin(page)
    expect(page.get_by_role("link", name="Ver todas as especialidades")).to_be_visible()
    expect(page.get_by_role("link", name="Ver todos os profissionais")).to_be_visible()
    expect(page.get_by_text("Especialidade QA Extra 12", exact=True)).to_be_visible(timeout=15000)
    # Verify the dashboard card itself rather than other areas referencing the specialty.
    specialty_panel = page.get_by_role("heading", name="Especialidades", exact=True).locator("xpath=../../../..")
    assert specialty_panel.locator('[role="listitem"]').count() == 3
    link = page.get_by_role("link", name="Ver todas as especialidades")
    assert link.evaluate("(el) => getComputedStyle(el).cursor") == "pointer"
    link.focus()
    link.press("Enter")
    expect(page).to_have_url(re.compile(r"/admin/especialidades/?$"), timeout=30000)
    page.get_by_role("button", name="Próxima").click()
    expect(page.locator('[role="listitem"]').get_by_text("Medicina QA Navegador", exact=True).first).to_be_visible(timeout=15000)
    expect(page.get_by_role("heading", name="Todas as especialidades")).to_be_visible()


def test_admin_specialty_search_and_professional_routes_at_mobile_width(page: Page) -> None:
    login_as_admin(page)
    for width, height in ((320, 640), (375, 667), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        page.emulate_media(reduced_motion="reduce")
        page.goto(BASE + "/admin/especialidades", wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name="Todas as especialidades")).to_be_visible(timeout=30000)
        page.locator("#specialty-directory-search").fill("Extra 2")
        expect(page.get_by_text("Especialidade QA Extra 2", exact=True)).to_be_visible(timeout=15000)
        expect(page.get_by_text("Especialidade QA Extra 1", exact=True)).not_to_be_visible()
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), overflowing_elements(page)
        page.locator("#specialty-directory-search").fill("")
        page.get_by_role("link", name="Voltar ao painel").click()
        expect(page).to_have_url(re.compile(r"/admin/?$"), timeout=30000)
        page.get_by_role("link", name="Ver todos os profissionais").click()
        expect(page).to_have_url(re.compile(r"/admin/profissionais/?$"), timeout=30000)
        expect(page.get_by_role("heading", name="Todos os profissionais")).to_be_visible(timeout=30000)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), overflowing_elements(page)
        page.screenshot(path=f"qa-artifacts/admin-diretorio-{width}px.png", full_page=True)


def test_non_admin_cannot_open_admin_directory_subroutes(page: Page) -> None:
    login(page, FIXTURE["doctor_b_email"])
    page.goto(BASE + "/admin/profissionais", wait_until="domcontentloaded")
    expect(page).to_have_url(re.compile(r"/acesso-negado/?$"), timeout=30000)
    expect(page.get_by_text("Dr. QA Extra 4")).to_have_count(0)


def test_admin_specialty_create_and_rename_keep_history(page: Page) -> None:
    """Exercise the actual create/edit modal handlers against disposable PostgreSQL."""
    login_as_admin(page)
    page.goto(BASE + "/admin/especialidades", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Todas as especialidades")).to_be_visible(timeout=30000)
    page.get_by_role("button", name="Nova especialidade").click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible(timeout=15000)
    dialog.locator("#specialty-create-name").fill("Área Clínica QA Nova")
    dialog.get_by_role("button", name="Cadastrar especialidade").click()
    expect(dialog).to_have_count(0, timeout=20000)
    row = page.locator('[role="listitem"]').filter(has_text="Área Clínica QA Nova")
    expect(row).to_be_visible(timeout=20000)
    row.get_by_role("button", name="Editar").click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible(timeout=15000)
    dialog.locator("#specialty-edit-name").fill("Área Clínica QA Renomeada")
    dialog.get_by_role("button", name="Salvar alterações").click()
    expect(dialog).to_have_count(0, timeout=20000)
    expect(page.locator('[role="listitem"]').filter(
        has_text="Área Clínica QA Renomeada"
    )).to_be_visible(timeout=20000)
    expect(page.locator('[role="listitem"]').filter(
        has_text="Área Clínica QA Nova"
    )).to_have_count(0)


def test_admin_registers_medical_professional_without_resend_and_prevents_duplicate(page: Page) -> None:
    """Real full-stack flow on a disposable database with no Resend API key."""
    login_as_admin(page)
    page.get_by_role("button", name="Novo profissional").click()
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible(timeout=15000)
    dialog.locator("#professional-name").fill("Dra. Onboarding QA")
    dialog.locator("#professional-email").fill("onboarding-qa@example.invalid")
    checkbox = dialog.get_by_role("checkbox", name="Especialidade QA Extra 2")
    checkbox.click()
    expect(checkbox).to_be_checked(timeout=15000)
    dialog.get_by_role("button", name="Cadastrar profissional").click()
    expect(dialog).to_have_count(0, timeout=30000)
    expect(page.get_by_text("Resend não configurado; e-mail não enviado.", exact=False)).to_be_visible(timeout=15000)

    page.goto(BASE + "/admin/profissionais", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Todos os profissionais")).to_be_visible(timeout=30000)
    row = page.locator('[role="listitem"]').filter(has_text="Dra. Onboarding QA")
    expect(row).to_be_visible(timeout=20000)
    expect(row.get_by_text("E-mail de acesso ainda não enviado.")).to_be_visible()

    page.get_by_role("button", name="Novo profissional").click()
    dialog = page.get_by_role("dialog")
    dialog.locator("#professional-name").fill("Dra. Duplicada QA")
    dialog.locator("#professional-email").fill("ONBOARDING-QA@example.invalid")
    checkbox = dialog.get_by_role("checkbox", name="Especialidade QA Extra 2")
    checkbox.click()
    expect(checkbox).to_be_checked(timeout=15000)
    dialog.get_by_role("button", name="Cadastrar profissional").click()
    expect(dialog).to_be_visible(timeout=15000)
    expect(dialog.get_by_text("Este e-mail já está vinculado a um profissional.")).to_be_visible(timeout=15000)


def test_admin_specialty_pagination_has_real_second_page(page: Page) -> None:
    """Exercise pagination with >10 specialties on disposable PostgreSQL."""
    login_as_admin(page)
    page.goto(BASE + "/admin/especialidades", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Todas as especialidades")).to_be_visible(timeout=30000)
    expect(page.get_by_text("Página 1 de 2", exact=True)).to_be_visible(timeout=20000)
    first_page = page.locator('[role="listitem"]')
    expect(first_page).to_have_count(10, timeout=15000)
    expect(page.get_by_role("button", name="Anterior")).to_be_disabled()
    page.get_by_role("button", name="Próxima").click()
    expect(page.get_by_text("Página 2 de 2", exact=True)).to_be_visible(timeout=15000)
    expect(page.get_by_role("button", name="Próxima")).to_be_disabled()
    page.get_by_role("button", name="Anterior").click()
    expect(page.get_by_text("Página 1 de 2", exact=True)).to_be_visible(timeout=15000)


def test_admin_availability_controls_are_understandable_and_responsive(page: Page) -> None:
    """Verify the operational calendar surface at three viewport sizes."""
    login_as_admin(page)
    for width, height in ((320, 640), (375, 667), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        page.emulate_media(reduced_motion="reduce")
        expect(page.get_by_role("heading", name="Horários de atendimento")).to_be_visible(timeout=30000)
        date = page.locator("#admin-slot-date")
        hour = page.locator("#admin-slot-time")
        expect(date).to_be_visible()
        expect(hour).to_be_visible()
        date.focus()
        expect(date).to_be_focused()
        date.press("Tab")
        expect(hour).to_be_focused()
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), overflowing_elements(page)
        page.screenshot(path=f"qa-artifacts/agenda-admin-{width}px.png", full_page=True)


def test_medical_registration_modal_mobile_form(page: Page) -> None:
    """Doctor onboarding fields remain understandable and operable on narrow screens."""
    login_as_admin(page)
    for width, height in ((320, 640), (375, 667), (768, 1024)):
        page.set_viewport_size({"width": width, "height": height})
        page.get_by_role("button", name="Novo profissional").click()
        dlg = page.get_by_role("dialog")
        expect(dlg).to_be_visible(timeout=15000)
        expect(dlg.locator("#professional-name")).to_be_visible()
        expect(dlg.locator("#professional-email")).to_be_visible()
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), overflowing_elements(page)
        page.screenshot(path=f"qa-artifacts/cadastro-medico-{width}px.png", full_page=True)
        dlg.locator("#professional-email").press("Escape")
        expect(dlg).to_have_count(0, timeout=15000)
