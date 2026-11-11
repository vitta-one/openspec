"""Capture all currently implemented Vitta-One screens in real Chromium.

Run only after real browser QA against the disposable PostgreSQL fixture.
Every protected route is visited through the appropriate authenticated role.
Screenshots and the manifest are stored as CI artifacts, never committed.
"""

import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("QA_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
OUTPUT = Path("qa-artifacts/screenshots")
FIXTURE = json.loads(Path("qa-artifacts/fixture.json").read_text(encoding="utf-8"))
PASSWORD = os.environ["VITTA_ONE_QA_PASSWORD"]
VIEWPORTS = {"desktop": (1440, 900), "tablet": (768, 1024), "mobile": (375, 812)}

# (slug, route, visible heading) — aligns with vitta_one/vitta_one.py routes.
SCREENS = {
    "public": [
        ("login", "/login", "Acesse sua conta"),
        ("ativacao-paciente", "/ativar-paciente", "Ative seu portal"),
    ],
    "administrador": [
        ("painel-admin", "/admin", "Gestão da clínica"),
        ("funcionarios", "/admin/funcionarios", "Funcionários"),
        ("funcionarios-novo", "/admin/funcionarios/novo", "Novo funcionário"),
        ("cadastro-medico", "/admin/funcionarios/medico", "Cadastrar médico"),
        ("cadastro-recepcionista", "/admin/funcionarios/recepcionista", "Cadastrar recepcionista"),
        ("horarios-admin", "/admin/horarios", "Gerenciar horários"),
        ("configuracoes", "/admin/configuracoes", "Configurações da clínica"),
        ("especialidades", "/admin/especialidades", "Todas as especialidades"),
        ("profissionais", "/admin/profissionais", "Todos os profissionais"),
        ("admin-previa-recepcao", "/admin/recepcao", "Recepção"),
        ("admin-previa-agenda", "/admin/agenda", "Agenda clínica"),
        ("admin-previa-atendimento", "/admin/atendimento", "Atendimento clínico"),
        ("admin-previa-pacientes", "/admin/pacientes", "Pacientes"),
        ("admin-financeiro", "/admin/financeiro", "Financeiro"),
    ],
    "recepcionista": [
        ("painel-recepcao", "/recepcao", "Recepção"),
        ("agenda-recepcao", "/recepcao/agenda", "Agenda e check-in"),
        ("lista-pacientes", "/recepcao/pacientes", "Lista de pacientes"),
        ("cadastro-pacientes", "/recepcao/pacientes/novo", "Novo paciente"),
        ("fila-espera", "/recepcao/fila", "Fila de espera"),
    ],
    "medico": [
        ("painel-medico", "/medico", "Visão geral do consultório"),
        ("prontuarios-medico", "/medico/prontuarios", "Registro clínico do paciente atual"),
        ("agenda-medico", "/medico/agenda", "Minha agenda"),
        ("pacientes-medico", "/medico/pacientes", "Pacientes vinculados"),
        ("impressao-prescricao", f"/medico/prescricao/{FIXTURE['prescription_id']}", None),
        ("acesso-negado", "/acesso-negado", "Esta área pertence a outra função."),
    ],
    "paciente": [
        ("portal-paciente", "/paciente", "Agenda do paciente"),
        ("agendamento-paciente", "/paciente/agendar", "Agendar consulta"),
    ],
    "financeiro": [("painel-financeiro", "/financeiro", "Financeiro")],
    "primeiro-acesso": [("primeiro-acesso", "/primeiro-acesso", "Defina sua nova senha")],
}

EMAILS = {
    "administrador": FIXTURE["admin_email"],
    "recepcionista": FIXTURE["reception_email"],
    "medico": FIXTURE["doctor_a_email"],
    "paciente": FIXTURE["patient_portal_email"],
    "financeiro": FIXTURE["finance_email"],
    "primeiro-acesso": FIXTURE["first_access_email"],
}
DASHBOARDS = {
    "administrador": "/admin",
    "recepcionista": "/recepcao",
    "medico": "/medico",
    "paciente": "/paciente",
    "financeiro": "/financeiro",
    "primeiro-acesso": "/primeiro-acesso",
}


def same_path(actual: str, expected: str) -> bool:
    return urlsplit(actual).path.rstrip("/") == expected.rstrip("/")


def authenticate(page, role: str) -> None:
    page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=30000)
    page.locator("#login-email").fill(EMAILS[role])
    page.locator("#login-password").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(re.compile(re.escape(BASE + DASHBOARDS[role]) + r"/?$"), timeout=30000)


def capture(page, role: str, item, viewport: str, failures: list, manifest: list) -> None:
    slug, route, heading = item
    file_name = f"{viewport}-{role}-{slug}.png"
    screenshot_path = OUTPUT / file_name
    errors = []
    record = {"role": role, "screen": slug, "route": route, "viewport": viewport,
              "file": str(screenshot_path), "status": "PASS"}
    page_errors = []
    def collect_page_error(error):
        page_errors.append(error)

    page.on("pageerror", collect_page_error)
    try:
        page.goto(BASE + route, wait_until="domcontentloaded", timeout=30000)
        expect(page).to_have_url(re.compile(re.escape(BASE + route) + r"/?$"), timeout=30000)
        if heading:
            expect(page.get_by_role("heading", name=heading, exact=True).first).to_be_visible(timeout=30000)
        else:
            expect(page.get_by_text(FIXTURE["patient_name"], exact=False).first).to_be_visible(timeout=30000)
        assert page.locator("body").inner_text().strip(), "Tela vazia"
        assert not page.locator("nextjs-portal, vite-error-overlay").count(), "Overlay de erro"
        overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2")
        assert not overflow, "Overflow horizontal da página"
        if page_errors:
            raise AssertionError("Exceção JavaScript no navegador: " + str(page_errors[0])[:220])
    except Exception as exc:
        errors.append(str(exc)[:600])
    finally:
        try:
            page.screenshot(path=str(screenshot_path), full_page=True, animations="disabled", timeout=15000)
        except Exception as exc:
            errors.append("Screenshot não gerado: " + str(exc)[:220])
        if errors:
            record["status"] = "FAIL"
            record["errors"] = errors
            failures.append(f"{viewport}/{role}/{slug}: {'; '.join(errors)}")
        manifest.append(record)
        page.remove_listener("pageerror", collect_page_error)


def main() -> None:
    if os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes":
        raise RuntimeError("Captura permitida apenas em ambiente QA descartável")
    if os.environ.get("VITTA_ONE_LOCAL_ADMIN_PREVIEW", "").lower() != "true":
        raise RuntimeError("As prévias do Administrador exigem QA local explicitamente habilitado")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest, failures = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for viewport, (width, height) in VIEWPORTS.items():
                for role, screens in SCREENS.items():
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        locale="pt-BR", reduced_motion="reduce",
                        color_scheme="light", device_scale_factor=1,
                        is_mobile=viewport == "mobile", has_touch=viewport == "mobile",
                    )
                    page = context.new_page()
                    try:
                        if role != "public":
                            authenticate(page, role)
                        for screen in screens:
                            capture(page, role, screen, viewport, failures, manifest)
                    except Exception as exc:
                        message = f"{viewport}/{role}: login ou inicialização falhou: {str(exc)[:500]}"
                        failures.append(message)
                        for screen in screens:
                            manifest.append({"role": role, "screen": screen[0],
                                             "viewport": viewport, "route": screen[1],
                                             "status": "BLOCKED", "error": message})
                    finally:
                        context.close()
        finally:
            browser.close()

    (OUTPUT / "manifest.json").write_text(
        json.dumps({"base_url": BASE, "captures": manifest, "failures": failures},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    passed = sum(item["status"] == "PASS" for item in manifest)
    print(f"QA visual: {passed}/{len(manifest)} telas/formatos validados. Diretório: {OUTPUT}")
    if failures:
        raise AssertionError("QA visual falhou:\n" + "\n".join(failures))


if __name__ == "__main__":
    main()
