"""Capture and compare the sixteen operational routes on disposable QA data.

The reference PNGs stay local under VITTA_ONE_REFERENCE_DIR and are never copied
into the repository. Browser captures, visual pairs and their manifest are kept
under the ignored qa-artifacts/ directory.
"""

import base64
import json
import os
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from qa_browser.playwright_support import (
    launch_chromium,
    validate_disposable_database_url,
    validate_loopback_base_url,
)


BASE = validate_loopback_base_url(
    os.environ.get("QA_BASE_URL", "http://127.0.0.1:3000")
)
REFERENCE_DIR = Path(os.environ.get(
    "VITTA_ONE_REFERENCE_DIR", ".codex-vitta-ref/referencias"
)).resolve()
CAPTURE_ONLY = os.environ.get("VITTA_ONE_QA_CAPTURE_ONLY") == "yes"
REFERENCE_AVAILABLE = False
ROOT_OUTPUT = Path("qa-artifacts/operational-reference")
SCREEN_OUTPUT = ROOT_OUTPUT / "screenshots"
COMPARISON_OUTPUT = ROOT_OUTPUT / "comparisons"
FIXTURE = json.loads(Path("qa-artifacts/fixture.json").read_text(encoding="utf-8"))
PASSWORD = os.environ["VITTA_ONE_QA_PASSWORD"]

VIEWPORTS = {
    "desktop-1768x890": (1768, 890),
    "desktop-1440x900": (1440, 900),
    "tablet-1024x768": (1024, 768),
    "tablet-768x1024": (768, 1024),
    "mobile-390x844": (390, 844),
    "mobile-320x740": (320, 740),
}

SCREENS = [
    ("recepcionista", "01-dashboard-recepcao", "/recepcao", "Recepção"),
    ("recepcionista", "02-agenda-recepcao", "/recepcao/agenda", "Agenda e check-in"),
    ("recepcionista", "03-lista-pacientes", "/recepcao/pacientes", "Lista de pacientes"),
    ("recepcionista", "04-novo-paciente", "/recepcao/pacientes/novo", "Novo paciente"),
    ("recepcionista", "05-fila-espera", "/recepcao/fila", "Fila de espera"),
    ("administrador", "06-dashboard-administracao", "/admin", "Gestão da clínica"),
    ("administrador", "07-funcionarios", "/admin/funcionarios", "Funcionários"),
    ("administrador", "08-novo-funcionario", "/admin/funcionarios/novo", "Novo funcionário"),
    ("administrador", "09-especialidades", "/admin/especialidades", "Todas as especialidades"),
    ("administrador", "10-gerenciar-horarios", "/admin/horarios", "Gerenciar horários"),
    ("administrador", "11-configuracoes-clinica", "/admin/configuracoes", "Configurações da clínica"),
    ("financeiro", "12-financeiro-asaas", "/financeiro", "Financeiro"),
    ("medico", "13-medico-visao-geral", "/medico", "Visão geral do consultório"),
    ("medico", "14-medico-agenda", "/medico/agenda", "Minha agenda"),
    ("medico", "15-medico-pacientes", "/medico/pacientes", "Pacientes vinculados"),
    ("medico", "16-medico-prontuarios", "/medico/prontuarios", "Registro clínico do paciente atual"),
]

EMAILS = {
    "administrador": FIXTURE["admin_email"],
    "recepcionista": FIXTURE["reception_email"],
    "medico": FIXTURE["doctor_a_email"],
    "financeiro": FIXTURE["finance_email"],
}
DASHBOARDS = {
    "administrador": "/admin",
    "recepcionista": "/recepcao",
    "medico": "/medico",
    "financeiro": "/financeiro",
}


def _assert_disposable_database() -> None:
    global REFERENCE_AVAILABLE
    validate_disposable_database_url(
        os.environ.get("DATABASE_URL", ""),
        enabled=os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE", ""),
        database_id=os.environ.get("VITTA_ONE_QA_DISPOSABLE_DATABASE_ID", ""),
    )
    if not REFERENCE_DIR.is_dir():
        if CAPTURE_ONLY:
            return
        raise RuntimeError("Diretório local das 16 referências não encontrado")
    found = sorted(path.name for path in REFERENCE_DIR.glob("*.png"))
    expected = sorted(f"{slug}.png" for _, slug, _, _ in SCREENS)
    if found != expected:
        raise RuntimeError(f"Esperadas 16 referências PNG únicas; encontrados {len(found)}")
    REFERENCE_AVAILABLE = True


def _authenticate(page, role: str) -> None:
    page.goto(BASE + "/login", wait_until="domcontentloaded", timeout=30000)
    page.locator("#login-email").fill(EMAILS[role])
    page.locator("#login-password").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(
        re.compile(re.escape(BASE + DASHBOARDS[role]) + r"/?$"), timeout=30000
    )


def _capture(page, viewport_name: str, spec, failures: list[dict], records: list[dict]) -> None:
    role, slug, route, heading = spec
    output = SCREEN_OUTPUT / viewport_name / f"{slug}.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    page_errors: list[str] = []
    on_page_error = lambda error: page_errors.append(str(error))
    page.on("pageerror", on_page_error)
    try:
        page.goto(BASE + route, wait_until="domcontentloaded", timeout=30000)
        expect(page).to_have_url(
            re.compile(re.escape(BASE + route) + r"/?$"), timeout=30000
        )
        expect(page.get_by_role("heading", name=heading, exact=True).first).to_be_visible(
            timeout=30000
        )
        if route == "/recepcao/agenda":
            expect(page.locator(".vitta-reception-calendar-event").first).to_be_visible(
                timeout=30000
            )
            expect(page.locator(".vitta-reception-calendar-grid-body")).to_be_visible(
                timeout=30000
            )
            headers = page.locator(".vitta-reception-calendar-grid-header > *")
            expect(headers).to_have_count(8)
            view_select = page.get_by_role("combobox", name="Visualização da agenda")
            view_select.click()
            page.get_by_role("option", name="Dia", exact=True).click()
            expect(headers).to_have_count(2)
            view_select.click()
            page.get_by_role("option", name="Semana", exact=True).click()
            expect(headers).to_have_count(8)
            page.evaluate("document.activeElement && document.activeElement.blur()")
        if not page.locator("body").inner_text().strip():
            raise AssertionError("A rota não renderizou conteúdo")
        if page.locator("nextjs-portal, vite-error-overlay").count():
            raise AssertionError("Overlay de erro de desenvolvimento visível")
        if page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"):
            raise AssertionError("Overflow horizontal da página")
        if page_errors:
            raise AssertionError("Erro JavaScript: " + page_errors[0][:220])
    except Exception as error:  # keep the remaining routes/screens observable
        errors.append(str(error)[:500])
    finally:
        try:
            page.screenshot(path=str(output), full_page=False, animations="disabled", timeout=15000)
        except Exception as error:
            errors.append("Screenshot não gerado: " + str(error)[:220])
        record = {
            "role": role,
            "screen": slug,
            "route": route,
            "viewport": viewport_name,
            "file": str(output),
            "status": "FAIL" if errors else "PASS",
        }
        if errors:
            record["errors"] = errors
            failures.append(record)
        records.append(record)
        page.remove_listener("pageerror", on_page_error)


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _create_comparison_images(browser, desktop_records: list[dict]) -> None:
    COMPARISON_OUTPUT.mkdir(parents=True, exist_ok=True)
    desktop = {item["screen"]: Path(item["file"]) for item in desktop_records}
    page = browser.new_page(viewport={"width": 1768, "height": 600}, device_scale_factor=1)
    try:
        for group_start in range(0, len(SCREENS), 4):
            group = SCREENS[group_start:group_start + 4]
            cards = []
            for _role, slug, _route, _heading in group:
                reference = _data_uri(REFERENCE_DIR / f"{slug}.png")
                capture = _data_uri(desktop[slug])
                cards.append(
                    f'<article><h2>{slug}</h2><div class="pair">'
                    f'<figure><figcaption>Referência</figcaption><img src="{reference}"></figure>'
                    f'<figure><figcaption>Chromium 1768 × 890</figcaption><img src="{capture}"></figure>'
                    "</div></article>"
                )
            html = """<!doctype html><meta charset="utf-8"><style>
            *{box-sizing:border-box}body{margin:0;padding:14px;background:#f1f5f9;color:#0f172a;
            font:14px/1.4 Arial,sans-serif}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
            article{min-width:0;padding:9px;background:white;border:1px solid #cbd5e1;border-radius:8px}
            h2{font-size:13px;margin:0 0 6px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:5px}
            figure{margin:0;min-width:0}figcaption{font-size:11px;color:#475569;margin-bottom:3px}
            img{display:block;width:100%;height:auto;border:1px solid #dbe2ea}
            </style><main class="grid">""" + "".join(cards) + "</main>"
            page.set_content(html, wait_until="load")
            page.screenshot(
                path=str(COMPARISON_OUTPUT / f"comparativo-{group_start + 1:02d}-{group_start + 4:02d}.png"),
                full_page=True,
                animations="disabled",
            )
    finally:
        page.close()


def main() -> None:
    _assert_disposable_database()
    ROOT_OUTPUT.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []
    records: list[dict] = []
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright)
        try:
            for viewport_name, (width, height) in VIEWPORTS.items():
                roles = tuple(dict.fromkeys(role for role, *_ in SCREENS))
                for role in roles:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        locale="pt-BR",
                        reduced_motion="reduce",
                        color_scheme="light",
                        device_scale_factor=1,
                        is_mobile=width < 480,
                        has_touch=width < 480,
                    )
                    page = context.new_page()
                    try:
                        _authenticate(page, role)
                        for screen in (spec for spec in SCREENS if spec[0] == role):
                            _capture(page, viewport_name, screen, failures, records)
                    except Exception as error:
                        failure = {
                            "role": role,
                            "viewport": viewport_name,
                            "status": "BLOCKED",
                            "error": str(error)[:500],
                        }
                        failures.append(failure)
                        for spec in (item for item in SCREENS if item[0] == role):
                            records.append({
                                "role": role,
                                "screen": spec[1],
                                "route": spec[2],
                                "viewport": viewport_name,
                                "status": "BLOCKED",
                            })
                    finally:
                        context.close()
            desktop_records = [
                item for item in records
                if item.get("viewport") == "desktop-1768x890" and item.get("status") == "PASS"
            ]
            if REFERENCE_AVAILABLE and len(desktop_records) == len(SCREENS):
                _create_comparison_images(browser, desktop_records)
        finally:
            browser.close()

    manifest = {
        "base_url": BASE,
        "reference_directory": str(REFERENCE_DIR) if REFERENCE_AVAILABLE else None,
        "comparison_generated": REFERENCE_AVAILABLE and len(desktop_records) == len(SCREENS),
        "viewports": {name: {"width": width, "height": height}
                      for name, (width, height) in VIEWPORTS.items()},
        "captures": records,
        "failures": failures,
    }
    (ROOT_OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    passed = sum(item["status"] == "PASS" for item in records)
    mode = "com comparação local" if REFERENCE_AVAILABLE else "somente capturas; referências locais ausentes"
    print(f"Capturas operacionais: {passed}/{len(records)} PASS ({mode}); artefatos em {ROOT_OUTPUT}")
    if failures:
        raise AssertionError(f"Falhas de QA visual/interativo: {len(failures)}")


if __name__ == "__main__":
    main()
