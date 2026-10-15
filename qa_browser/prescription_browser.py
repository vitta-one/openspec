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
        # Native date controls have browser-specific internal Tab stops.
        # Verify that the separate time input is directly keyboard-focusable.
        hour.focus()
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
        # Radix's modal can reserve hidden scroll-padding in the document's
        # scrollWidth. Verify the real rendered controls do not spill off-screen.
        assert not overflowing_elements(page), overflowing_elements(page)
        bounds = dlg.bounding_box()
        assert bounds is not None
        assert bounds["x"] >= -2 and bounds["x"] + bounds["width"] <= width + 2
        page.screenshot(path=f"qa-artifacts/cadastro-medico-{width}px.png", full_page=True)
        dlg.locator("#professional-email").press("Escape")
        expect(dlg).to_have_count(0, timeout=15000)


def login_as_reception(page: Page) -> None:
    """Authenticate a receptionist in disposable PostgreSQL browser QA."""
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    page.locator("#login-email").fill(FIXTURE["reception_email"])
    page.locator("#login-password").fill(os.environ["VITTA_ONE_QA_PASSWORD"])
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(re.compile(r"/recepcao/?$"), timeout=30000)
    expect(
        page.get_by_role("heading", name="Recepção — Operação do Dia", exact=True)
    ).to_be_visible(timeout=30000)
    expect(page.locator(".vitta-reception-day-table")).to_be_visible(timeout=30000)


def test_reception_daily_operations_table_and_filters(page: Page) -> None:
    """Reception works from real daily appointments, not an abstract KPI dashboard."""
    login_as_reception(page)
    expect(page.get_by_text(FIXTURE["day_first_patient_name"], exact=True)).to_be_visible()
    expect(page.locator(".vitta-reception-day-row")).to_have_count(7)
    expect(page.get_by_label("Página atual")).to_have_text("1 de 4")
    expect(page.get_by_role("status").filter(has_text="de 24 consultas de hoje")).to_be_visible()

    page.screenshot(path="qa-artifacts/dashboard-recepcao-1280px.png", full_page=True)

    # Search is server submitted and can locate a patient's phone number.
    search = page.locator("#reception-day-search")
    search.fill(FIXTURE["day_first_patient_phone"])
    search.press("Enter")
    expect(page.locator(".vitta-reception-day-row")).to_have_count(1, timeout=30000)
    expect(page.get_by_text(FIXTURE["day_first_patient_name"], exact=True)).to_be_visible()

    # Restore the day, then filter by a professional from the persisted directory.
    search.fill("")
    search.press("Enter")
    expect(page.locator(".vitta-reception-day-row")).to_have_count(7, timeout=30000)
    page.locator("#reception-day-professional").click()
    page.get_by_role("option", name=FIXTURE["day_first_professional_name"]).click()
    expect(page.locator(".vitta-reception-day-row")).to_have_count(7, timeout=30000)
    expect(page.get_by_role("status").filter(has_text="de 8 consultas de hoje")).to_be_visible()
    expect(page.get_by_label("Página atual")).to_have_text("1 de 2")

    # Paging stays keyboard operable and reflects the server-side page.
    page.get_by_role("button", name="Próxima página").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_label("Página atual")).to_have_text("2 de 2", timeout=30000)
    expect(page.locator(".vitta-reception-day-row")).to_have_count(1, timeout=30000)

    page.locator("#reception-day-professional").click()
    page.get_by_role("option", name="Todos os profissionais").click()
    expect(page.get_by_label("Página atual")).to_have_text("1 de 4", timeout=30000)


def test_reception_routes_and_responsive_daily_table(page: Page) -> None:
    login_as_reception(page)
    expect(page.get_by_role("button", name="Atualizar consultas de hoje")).to_be_visible()
    expect(page.get_by_role("link", name="Ir para Agenda")).to_be_visible()
    expect(page.get_by_role("button", name="Nova consulta")).to_be_visible()

    for width in (1280, 1264, 1200, 768, 375, 320):
        page.set_viewport_size({"width": width, "height": 760})
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 2"
        ), overflowing_elements(page)
        page.screenshot(
            path=f"qa-artifacts/dashboard-recepcao-{width}px.png",
            full_page=True,
        )

    for path, heading in (
        ("/recepcao/agenda", "Agenda e check-in"),
        ("/recepcao/pacientes", "Cadastro e localização"),
        ("/recepcao/fila", "Fila de espera"),
    ):
        page.goto(BASE + path, wait_until="domcontentloaded")
        expect(page.get_by_role("heading", name=heading)).to_be_visible(timeout=30000)
        for width in (320, 375, 768):
            page.set_viewport_size({"width": width, "height": 760})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth + 2"
            ), overflowing_elements(page)

    page.goto(BASE + "/recepcao", wait_until="domcontentloaded")
    expect(
        page.get_by_role("heading", name="Recepção — Operação do Dia", exact=True)
    ).to_be_visible(timeout=30000)


def test_reception_global_patient_search_uses_identity_only(page: Page) -> None:
    login_as_reception(page)
    search = page.locator("#topbar-patient-search")
    search.fill(FIXTURE["day_first_patient_name"])
    search.press("Enter")
    result = page.get_by_role(
        "button",
        name=f"Selecionar paciente {FIXTURE['day_first_patient_name']}",
    )
    expect(result).to_be_visible(timeout=30000)
    result.click()
    expect(page).to_have_url(re.compile(r"/recepcao/pacientes/?$"), timeout=30000)
    expect(page.get_by_text(FIXTURE["day_first_patient_name"], exact=True)).to_be_visible(
        timeout=30000
    )


def test_doctor_cannot_access_reception_dashboard_or_modules(page: Page) -> None:
    login(page, FIXTURE["doctor_b_email"])
    for path in ("/recepcao", "/recepcao/agenda", "/recepcao/pacientes", "/recepcao/fila"):
        page.goto(BASE + path, wait_until="domcontentloaded")
        expect(page).to_have_url(re.compile(r"/acesso-negado/?$"), timeout=30000)
        expect(
            page.get_by_text("Recepção — Operação do Dia", exact=True)
        ).to_have_count(0)


def test_reception_dashboard_is_read_only_and_refreshes(page: Page) -> None:
    login_as_reception(page)
    expect(page.locator(".vitta-reception-day-row")).to_have_count(7, timeout=30000)
    expect(page.get_by_role("button", name="Atualizar consultas de hoje")).to_be_visible()
    assert page.get_by_role("button", name=re.compile("Chamar próximo", re.I)).count() == 0
    assert page.get_by_role("button", name=re.compile("Finalizar atendimento", re.I)).count() == 0
    assert page.get_by_text("Sintoma histórico fictício QA", exact=False).count() == 0
    assert page.get_by_text("Medicamento Fictício QA", exact=False).count() == 0

    agenda_link = page.get_by_role("link", name=re.compile("Abrir Agenda para")).first
    expect(agenda_link).to_have_attribute("href", "/recepcao/agenda")
    page.get_by_role("button", name="Atualizar consultas de hoje").click()
    expect(page.locator(".vitta-reception-day-row")).to_have_count(7, timeout=30000)
    expect(page.locator(".vitta-reception-day-updated")).to_be_visible(timeout=30000)
