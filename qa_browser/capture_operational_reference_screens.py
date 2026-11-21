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
    ("administrador", "09-especialidades", "/admin/especialidades", "Especialidades"),
    ("administrador", "10-gerenciar-horarios", "/admin/horarios", "Gerenciar horários"),
    ("administrador", "11-configuracoes-clinica", "/admin/configuracoes", "Configurações da clínica"),
    ("financeiro", "12-financeiro-asaas", "/financeiro", "Financeiro"),
    ("medico", "13-medico-visao-geral", "/medico", "Visão geral do consultório"),
    ("medico", "14-medico-agenda", "/medico/agenda", "Minha agenda"),
    ("medico", "15-medico-pacientes", "/medico/pacientes", "Pacientes vinculados"),
    ("medico", "16-medico-prontuarios", "/medico/prontuarios", "Registro clínico do paciente atual"),
]

# These labels describe only the fixture class shown in each route. They never
# embed patient names, clinical content, counts, e-mail addresses, or identifiers.
DATA_STATES = {
    "01-dashboard-recepcao": "synthetic_persisted_metrics_and_appointments",
    "02-agenda-recepcao": "synthetic_persisted_appointments",
    "03-lista-pacientes": "synthetic_persisted_patient_directory",
    "04-novo-paciente": "initial_patient_form",
    "05-fila-espera": "synthetic_persisted_waiting_queue",
    "06-dashboard-administracao": "synthetic_persisted_admin_summary",
    "07-funcionarios": "synthetic_persisted_staff_directory",
    "08-novo-funcionario": "initial_staff_form",
    "09-especialidades": "synthetic_persisted_specialty_directory",
    "10-gerenciar-horarios": "no_professional_selected",
    "11-configuracoes-clinica": "clinic_configuration_unconfigured",
    "12-financeiro-asaas": "no_eligible_charges",
    "13-medico-visao-geral": "shared_synthetic_queue_without_active_doctor_record",
    "14-medico-agenda": "doctor_without_scheduled_consultations",
    "15-medico-pacientes": "doctor_without_linked_patients",
    "16-medico-prontuarios": "no_active_record_for_doctor",
}

EMAILS = {
    "administrador": FIXTURE["admin_email"],
    "recepcionista": FIXTURE["reception_email"],
    # Doctor B is a linked QA identity with an empty consultation projection in
    # the freshly seeded capture database. Browser booking tests may consume its
    # synthetic slot, so reference captures use a fresh fixture and never erase
    # those test results.
    "medico": FIXTURE["doctor_b_email"],
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
    websocket_errors: list[str] = []
    geometry: dict = {}
    on_page_error = lambda error: page_errors.append(str(error))
    page.on(
        "websocket",
        lambda socket: socket.on(
            "socketerror",
            lambda error: websocket_errors.append(f"{socket.url}: {error}"),
        ),
    )
    page.on("pageerror", on_page_error)
    try:
        page.goto(BASE + route, wait_until="domcontentloaded", timeout=30000)
        expect(page).to_have_url(
            re.compile(re.escape(BASE + route) + r"/?$"), timeout=30000
        )
        expect(page.get_by_role("heading", name=heading, exact=True).first).to_be_visible(
            timeout=30000
        )
        page.wait_for_function(
            "Array.from(document.images).every((image) => image.complete)",
            timeout=10000,
        )
        broken_images = page.locator("img").evaluate_all(
            "images => images.filter(image => image.naturalWidth === 0)"
            ".map(image => image.getAttribute('src') || image.currentSrc)"
        )
        if broken_images:
            raise AssertionError("Imagem não carregada: " + ", ".join(broken_images))
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
        if route == "/recepcao" and viewport_name == "desktop-1768x890":
            if page.locator(".vitta-reception-upcoming-row").count() > 3:
                raise AssertionError("A prévia do dashboard excedeu três próximos atendimentos")
            rows = page.locator(".vitta-reception-day-table tbody tr")
            first_page_row = rows.first.inner_text()
            page.get_by_role("button", name="2", exact=True).click()
            expect(page.get_by_role("button", name="2", exact=True)).to_have_attribute(
                "aria-current", "page", timeout=15000
            )
            expect(rows.first).not_to_have_text(first_page_row, timeout=15000)
            page.get_by_role("button", name="1", exact=True).click()
            expect(page.get_by_role("button", name="1", exact=True)).to_have_attribute(
                "aria-current", "page", timeout=15000
            )
        if route == "/admin/funcionarios" and viewport_name == "desktop-1768x890":
            page_size = page.get_by_role("combobox", name="Itens por página")
            expect(page_size).to_be_visible()
            page_size.click()
            page.get_by_role("option", name="25", exact=True).click()
            expect(page_size).to_contain_text("25")
            page_size.click()
            page.get_by_role("option", name="10", exact=True).click()
            expect(page_size).to_contain_text("10")
            expect(page.locator('.vitta-staff-page-control[aria-current="page"]')).to_have_text("1")
            page.evaluate("document.activeElement && document.activeElement.blur()")
        if route == "/admin/especialidades" and viewport_name == "desktop-1768x890":
            search_box = page.locator("#specialty-directory-search").bounding_box()
            status_box = page.locator("#specialty-status-filter").bounding_box()
            if search_box is None or status_box is None:
                raise AssertionError("Filtros de especialidades não foram renderizados")
            if abs(search_box["y"] - status_box["y"]) > 2:
                raise AssertionError("Busca e situação não estão alinhadas na grade")
        if route == "/medico/agenda" and viewport_name == "desktop-1768x890":
            expect(page.locator(".vitta-doctor-week-empty")).to_have_count(7)
        if not page.locator("body").inner_text().strip():
            raise AssertionError("A rota não renderizou conteúdo")
        if page.locator("nextjs-portal, vite-error-overlay").count():
            raise AssertionError("Overlay de erro de desenvolvimento visível")
        if page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 2"):
            raise AssertionError("Overflow horizontal da página")
        if route == "/recepcao/pacientes/novo" and viewport_name == "mobile-320x740":
            placeholder = page.locator("#patient-create-name").evaluate("""input => {
              const inputStyle = getComputedStyle(input);
              const placeholderStyle = getComputedStyle(input, "::placeholder");
              const canvas = document.createElement("canvas");
              const context = canvas.getContext("2d");
              context.font = placeholderStyle.font;
              const letterSpacing = placeholderStyle.letterSpacing === "normal"
                ? 0
                : Number.parseFloat(placeholderStyle.letterSpacing) || 0;
              const textWidth = context.measureText(input.placeholder).width
                + Math.max(0, input.placeholder.length - 1) * letterSpacing;
              const availableWidth = input.clientWidth
                - Number.parseFloat(inputStyle.paddingLeft)
                - Number.parseFloat(inputStyle.paddingRight);
              return {textWidth, availableWidth};
            }""")
            if placeholder["textWidth"] > placeholder["availableWidth"]:
                raise AssertionError(
                    "O placeholder do nome do paciente fica cortado em 320 px"
                )
        if page_errors:
            raise AssertionError("Erro JavaScript: " + page_errors[0][:220])
        if websocket_errors:
            raise AssertionError("Falha de WebSocket: " + websocket_errors[0][:220])
        if "Cannot connect to server: websocket error." in page.locator("body").inner_text():
            raise AssertionError("Aviso de desconexão Reflex visível na captura")
        geometry = page.evaluate("""() => {
          const rect = (node) => {
            if (!node) return null;
            const box = node.getBoundingClientRect();
            return Object.fromEntries(['x', 'y', 'width', 'height'].map((key) =>
              [key, Math.round(box[key] * 100) / 100]
            ));
          };
          const first = (selector) => rect(document.querySelector(selector));
          const styleSnapshot = (node) => {
            if (!node) return null;
            const style = getComputedStyle(node);
            return {
              display: style.display,
              gap: style.gap,
              gridTemplateColumns: style.gridTemplateColumns,
              alignItems: style.alignItems,
              justifyContent: style.justifyContent,
              padding: style.padding,
              margin: style.margin,
              fontFamily: style.fontFamily,
              fontSize: style.fontSize,
              fontWeight: style.fontWeight,
              lineHeight: style.lineHeight,
              letterSpacing: style.letterSpacing,
              borderRadius: style.borderRadius,
              overflowWrap: style.overflowWrap
            };
          };
          const landmarks = [
            '.vitta-page-header', '.vitta-page-header .rt-Heading',
            '.vitta-admin-hub-metrics', '.vitta-reception-operations',
            '.vitta-reception-day-panel', '.vitta-patient-directory-workspace',
            '.vitta-patient-create-workspace', '.vitta-queue-active-panel',
            '.vitta-staff-form', '.vitta-specialty-table',
            '.vitta-availability-panel', '.vitta-clinic-settings-layout',
            '.vitta-clinic-settings-guidance', '.vitta-finance-filters',
            '.vitta-finance-issue', '.vitta-finance-charges',
            '.vitta-doctor-overview-grid', '.vitta-doctor-agenda-cta',
            '.vitta-doctor-week', '.vitta-doctor-week-heading',
            '.vitta-doctor-calendar', '.vitta-doctor-calendar-panel',
            '.vitta-doctor-active-empty-panel',
            '.vitta-doctor-patient-list', '.vitta-doctor-patient-heading',
            '.vitta-doctor-patient-empty .vitta-empty-state',
            '.vitta-doctor-records-empty-panel',
            '.vitta-doctor-records-empty-panel .vitta-empty-state',
            '.vitta-medical-history',
            '.vitta-clinic-settings-form', '.vitta-clinic-settings-heading',
            '.vitta-clinic-settings-actions', '#clinic-configuration-name',
            '#clinic-configuration-address', '.vitta-page-header-art'
          ];
          const main = document.querySelector('main.vitta-page');
          const headings = main ? Array.from(main.querySelectorAll('.rt-Heading')).map((node) => ({
            text: (node.innerText || '').trim().slice(0, 72),
            ...rect(node)
          })) : [];
          const patientEmpty = document.querySelector('.vitta-doctor-patient-empty .vitta-empty-state');
          const patientEmptyStyle = patientEmpty ? getComputedStyle(patientEmpty) : null;
          return {
            viewport: { width: innerWidth, height: innerHeight },
            sidebar: first('.vitta-sidebar'),
            topbar: first('.vitta-topbar'),
            page: rect(main),
            pageComputedStyle: styleSnapshot(main),
            breadcrumb: first('.vitta-breadcrumb'),
            title: first('.vitta-page-header .rt-Heading'),
            contentPadding: main ? {
              left: getComputedStyle(main).paddingLeft,
              top: getComputedStyle(main).paddingTop
            } : null,
            headings,
            images: Array.from(document.images).map((image) => ({
              src: image.getAttribute('src') || image.currentSrc,
              loaded: image.complete && image.naturalWidth > 0,
              width: image.naturalWidth,
              height: image.naturalHeight
            })),
            patientEmptyBackground: patientEmptyStyle ? {
              image: patientEmptyStyle.backgroundImage,
              size: patientEmptyStyle.backgroundSize,
              position: patientEmptyStyle.backgroundPosition
            } : null,
            landmarks: Object.fromEntries(landmarks.map((selector) =>
              [selector, first(selector)]
            )),
            landmarkStyles: Object.fromEntries(landmarks.map((selector) =>
              [selector, styleSnapshot(document.querySelector(selector))]
            )),
            sidebarLinks: Array.from(document.querySelectorAll(
              '.vitta-sidebar-nav .vitta-nav-link'
            )).map((node) => ({
              label: node.getAttribute('aria-label') || '',
              ...rect(node),
              computedStyle: styleSnapshot(node)
            })),
            pageChildren: main ? Array.from(main.children).map((node) => ({
              className: typeof node.className === 'string' ? node.className.slice(0, 120) : '',
              ...rect(node)
            })) : []
          };
        }""")
        if viewport_name == "desktop-1768x890" and route in {
            "/medico/agenda", "/medico/pacientes", "/medico/prontuarios"
        }:
            geometry["doctor_reference_landmarks"] = page.evaluate("""() => {
              const box = (selector) => {
                const node = document.querySelector(selector);
                if (!node) return null;
                const rect = node.getBoundingClientRect();
                return Object.fromEntries(['x', 'y', 'width', 'height'].map((key) =>
                  [key, Math.round(rect[key] * 100) / 100]
                ));
              };
              return Object.fromEntries([
                '.vitta-doctor-week-panel', '.vitta-agenda-week-grid',
                '.vitta-doctor-calendar-panel', '.vitta-doctor-month-heading-icon',
                '.vitta-doctor-month-divider', '.vitta-doctor-month-nav',
                '.vitta-doctor-month-weekdays', '.vitta-doctor-month-days',
                '.vitta-page-header', '.vitta-page-header .rt-Heading',
                '.vitta-doctor-patient-list', '.vitta-doctor-patient-heading-icon',
                '.vitta-doctor-patient-heading .rt-Heading',
                '.vitta-doctor-patient-empty .vitta-empty-state',
                '.vitta-breadcrumb', '.vitta-page-header-art',
                '.vitta-doctor-records-workspace',
                '.vitta-doctor-records-empty-panel .vitta-empty-state'
              ].map((selector) => [selector, box(selector)]));
            }""")
            expected_landmarks = {
                "/medico/agenda": {
                    ".vitta-doctor-week-panel": {"y": 319, "height": 254},
                    ".vitta-agenda-week-grid": {"y": 408},
                    ".vitta-doctor-calendar-panel": {"y": 592},
                    ".vitta-doctor-month-heading-icon": {"x": 343, "y": 600},
                    ".vitta-doctor-month-divider": {"y": 664},
                    ".vitta-doctor-month-nav": {"y": 676},
                    ".vitta-doctor-month-weekdays": {"y": 736},
                    ".vitta-doctor-month-days": {"y": 766},
                },
                "/medico/pacientes": {
                    ".vitta-page-header": {"x": 312, "y": 75, "width": 1424, "height": 176},
                    ".vitta-page-header .rt-Heading": {"x": 334, "y": 123},
                    ".vitta-doctor-patient-list": {"x": 312, "y": 279, "width": 1424, "height": 380},
                    ".vitta-doctor-patient-heading-icon": {"x": 343, "y": 294, "width": 70, "height": 68},
                    ".vitta-doctor-patient-heading .rt-Heading": {"x": 430, "y": 294},
                    ".vitta-doctor-patient-empty .vitta-empty-state": {"x": 335, "y": 378, "width": 1378, "height": 256},
                },
                "/medico/prontuarios": {
                    ".vitta-breadcrumb": {"x": 310, "y": 75},
                    ".vitta-page-header .rt-Heading": {"x": 320, "y": 192},
                    ".vitta-page-header-art": {"x": 995, "y": 88, "width": 753, "height": 228},
                    ".vitta-doctor-records-workspace": {"x": 310, "y": 316, "width": 1438},
                    ".vitta-doctor-records-empty-panel .vitta-empty-state": {"x": 333, "y": 341, "width": 1392, "height": 355},
                },
            }
            measured = geometry["doctor_reference_landmarks"]
            for selector, expected in expected_landmarks[route].items():
                actual = measured.get(selector)
                if actual is None:
                    raise AssertionError(f"Landmarka médica ausente: {selector}")
                for dimension, target in expected.items():
                    if abs(actual[dimension] - target) > 2:
                        raise AssertionError(
                            f"{route} {selector} {dimension}={actual[dimension]}px; "
                            f"referência {target}px"
                        )
        if route == "/admin/especialidades":
            geometry["specialty_filters"] = page.evaluate("""() => {
              const measure = (selector) => {
                const element = document.querySelector(selector);
                if (!element) return null;
                const box = element.getBoundingClientRect();
                const style = getComputedStyle(element);
                return {
                  rect: Object.fromEntries(['x', 'y', 'width', 'height'].map((key) =>
                    [key, Math.round(box[key] * 100) / 100]
                  )),
                  computed: {
                    height: style.height,
                    minHeight: style.minHeight,
                    paddingTop: style.paddingTop,
                    paddingBottom: style.paddingBottom,
                    lineHeight: style.lineHeight,
                    boxSizing: style.boxSizing
                  }
                };
              };
              return {
                search: measure('#specialty-directory-search'),
                status: measure('#specialty-status-filter')
              };
            }""")
        if route == "/financeiro":
            geometry["finance_forms"] = page.evaluate("""() => {
              const measure = (node) => {
                if (!node) return null;
                const box = node.getBoundingClientRect();
                const style = getComputedStyle(node);
                return {
                  rect: Object.fromEntries(['x', 'y', 'width', 'height'].map((key) =>
                    [key, Math.round(box[key] * 100) / 100]
                  )),
                  computed: {
                    display: style.display,
                    gap: style.gap,
                    columnGap: style.columnGap,
                    rowGap: style.rowGap,
                    padding: style.padding,
                    margin: style.margin,
                    fontSize: style.fontSize,
                    lineHeight: style.lineHeight,
                    height: style.height,
                    minHeight: style.minHeight
                  }
                };
              };
              const form = (selector) => {
                const root = document.querySelector(selector);
                if (!root) return null;
                return {
                  ...measure(root),
                  fields: Array.from(root.children).map((field) => ({
                    label: field.querySelector('p')?.innerText?.trim() ||
                      field.innerText.trim().slice(0, 48),
                    ...measure(field),
                    labelBox: measure(field.querySelector('p')),
                    controls: Array.from(field.querySelectorAll(
                      'input, button, [role="combobox"]'
                    )).map((control) => ({
                      name: control.getAttribute('name') ||
                        control.getAttribute('aria-label') ||
                        control.innerText.trim().slice(0, 48),
                      ...measure(control)
                    }))
                  }))
                };
              };
              return {
                filtersPanel: measure(document.querySelector('.vitta-finance-filters')),
                filterForm: form('.vitta-finance-filters-form'),
                issuePanel: measure(document.querySelector('.vitta-finance-issue')),
                issueLayout: measure(document.querySelector('.vitta-finance-issue-layout')),
                issueIcon: measure(document.querySelector('.vitta-finance-issue-icon')),
                issueForm: form('.vitta-finance-issue-form')
              };
            }""")
    except Exception as error:  # keep the remaining routes/screens observable
        errors.append(str(error)[:500])
    finally:
        try:
            # Route-specific interaction checks can scroll controls into view.
            # Capture the canonical top-of-page composition after those checks.
            page.evaluate("""() => {
              document.activeElement?.blur();
              window.scrollTo(0, 0);
            }""")
            page.wait_for_timeout(350)
            if "Cannot connect to server: websocket error." in page.locator("body").inner_text():
                raise AssertionError("Aviso de desconexão Reflex visível na captura")
            if websocket_errors:
                raise AssertionError("Falha de WebSocket: " + websocket_errors[0][:220])
            page.screenshot(path=str(output), full_page=False, animations="disabled", timeout=15000)
        except Exception as error:
            errors.append("Screenshot não gerado: " + str(error)[:220])
        record = {
            "role": role,
            "screen": slug,
            "route": route,
            "viewport": viewport_name,
            "data_state": DATA_STATES[slug],
            "data_origin": "disposable_synthetic_postgresql_qa",
            "file": str(output),
            "status": "FAIL" if errors else "PASS",
        }
        if geometry:
            record["geometry"] = geometry
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
    comparison_records: list[dict] = []
    page = browser.new_page(viewport={"width": 1768, "height": 600}, device_scale_factor=1)
    try:
        for _role, slug, _route, _heading in SCREENS:
            reference_path = REFERENCE_DIR / f"{slug}.png"
            capture_path = desktop.get(slug)
            if capture_path is None or not capture_path.is_file():
                comparison_records.append({
                    "screen": slug,
                    "status": "SKIP",
                    "reason": "Captura desktop válida não disponível",
                })
                continue

            output_dir = COMPARISON_OUTPUT / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            reference = _data_uri(reference_path)
            capture = _data_uri(capture_path)
            page.set_content(
                "<!doctype html><html><body><script>document.body.dataset.ready='1'</script></body></html>",
                wait_until="load",
            )
            result = page.evaluate(
                """async ({reference, capture}) => {
                    const load = (src) => new Promise((resolve, reject) => {
                      const image = new Image();
                      image.onload = () => resolve(image);
                      image.onerror = reject;
                      image.src = src;
                    });
                    const [referenceImage, captureImage] = await Promise.all([
                      load(reference), load(capture)
                    ]);
                    const width = 1768;
                    const height = 890;
                    if (captureImage.naturalWidth !== width || captureImage.naturalHeight !== height) {
                      throw new Error(`Captura com dimensão inesperada: ${captureImage.naturalWidth}x${captureImage.naturalHeight}`);
                    }
                    const frame = document.createElement('canvas');
                    frame.width = width;
                    frame.height = height;
                    const frameContext = frame.getContext('2d', {willReadFrequently: true});
                    frameContext.fillStyle = '#f7f8fc';
                    frameContext.fillRect(0, 0, width, height);
                    const scale = Math.min(width / referenceImage.naturalWidth, height / referenceImage.naturalHeight);
                    const drawWidth = referenceImage.naturalWidth * scale;
                    const drawHeight = referenceImage.naturalHeight * scale;
                    const offsetX = (width - drawWidth) / 2;
                    const offsetY = (height - drawHeight) / 2;
                    frameContext.drawImage(referenceImage, offsetX, offsetY, drawWidth, drawHeight);
                    const alignedReference = frame.toDataURL('image/png');
                    const referencePixels = frameContext.getImageData(0, 0, width, height).data;
                    const actual = document.createElement('canvas');
                    actual.width = width;
                    actual.height = height;
                    const actualContext = actual.getContext('2d', {willReadFrequently: true});
                    actualContext.drawImage(captureImage, 0, 0, width, height);
                    const actualPixels = actualContext.getImageData(0, 0, width, height).data;
                    const overlay = document.createElement('canvas');
                    overlay.width = width;
                    overlay.height = height;
                    const overlayContext = overlay.getContext('2d');
                    overlayContext.drawImage(frame, 0, 0);
                    overlayContext.globalAlpha = .5;
                    overlayContext.drawImage(actual, 0, 0);
                    overlayContext.globalAlpha = 1;
                    const overlayPng = overlay.toDataURL('image/png');
                    const difference = document.createElement('canvas');
                    difference.width = width;
                    difference.height = height;
                    const differenceContext = difference.getContext('2d');
                    const differencePixels = differenceContext.createImageData(width, height);
                    let totalDifference = 0;
                    let changedPixels = 0;
                    for (let index = 0; index < referencePixels.length; index += 4) {
                      let pixelDifference = 0;
                      for (let channel = 0; channel < 3; channel += 1) {
                        const delta = Math.abs(referencePixels[index + channel] - actualPixels[index + channel]);
                        pixelDifference += delta;
                        totalDifference += delta;
                        differencePixels.data[index + channel] = Math.min(255, delta * 3);
                      }
                      if (pixelDifference >= 36) changedPixels += 1;
                      differencePixels.data[index + 3] = 255;
                    }
                    differenceContext.putImageData(differencePixels, 0, 0);
                    const pair = document.createElement('canvas');
                    pair.width = width * 2;
                    pair.height = height;
                    const pairContext = pair.getContext('2d');
                    pairContext.drawImage(frame, 0, 0);
                    pairContext.drawImage(actual, width, 0);
                    return {
                      alignedReference,
                      overlay: overlayPng,
                      difference: difference.toDataURL('image/png'),
                      sideBySide: pair.toDataURL('image/png'),
                      referenceSize: [referenceImage.naturalWidth, referenceImage.naturalHeight],
                      captureSize: [captureImage.naturalWidth, captureImage.naturalHeight],
                      alignment: {scale, offsetX, offsetY, drawWidth, drawHeight},
                      metrics: {
                        meanAbsoluteChannelDifference: totalDifference / (width * height * 3),
                        changedPixelPercentAt36: 100 * changedPixels / (width * height),
                        thresholdRgbL1: 36,
                        masksApplied: false
                      }
                    };
                }""",
                {"reference": reference, "capture": capture},
            )
            for key, filename in (
                ("alignedReference", "reference-aligned.png"),
                ("overlay", "overlay-50.png"),
                ("difference", "diff-amplified-3x.png"),
                ("sideBySide", "side-by-side.png"),
            ):
                encoded = result[key].split(",", 1)[1]
                (output_dir / filename).write_bytes(base64.b64decode(encoded))
            comparison_records.append({
                "screen": slug,
                "reference": str(reference_path),
                "capture": str(capture_path),
                "data_state": DATA_STATES[slug],
                "data_origin": "disposable_synthetic_postgresql_qa",
                "output_directory": str(output_dir),
                "status": "GENERATED_REQUIRES_HUMAN_REVIEW",
                "reference_size": result["referenceSize"],
                "capture_size": result["captureSize"],
                "alignment": result["alignment"],
                "metrics": result["metrics"],
                "artifacts": {
                    "reference_aligned": str(output_dir / "reference-aligned.png"),
                    "overlay_50": str(output_dir / "overlay-50.png"),
                    "diff_amplified_3x": str(output_dir / "diff-amplified-3x.png"),
                    "side_by_side": str(output_dir / "side-by-side.png"),
                },
            })

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
    (ROOT_OUTPUT / "comparison-manifest.json").write_text(
        json.dumps({
            "reference_directory": str(REFERENCE_DIR),
            "frame": {"width": 1768, "height": 890, "fit": "contain", "background": "#f7f8fc"},
            "dynamic_masks": [],
            "comparisons": comparison_records,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (ROOT_OUTPUT / "fidelity-assessment.json").write_text(
        json.dumps({
            "status": "REVIEW_REQUIRED",
            "note": "Pixel metrics are diagnostic only; each route needs visual review before a parity rating.",
            "screens": [
                {
                    "screen": item["screen"],
                    "data_state": item["data_state"],
                    "assessment": "REVIEW_REQUIRED",
                }
                for item in comparison_records
            ],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
                                "data_state": DATA_STATES[spec[1]],
                                "data_origin": "disposable_synthetic_postgresql_qa",
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
    (ROOT_OUTPUT / "capture-manifest.json").write_text(
        json.dumps({
            "kind": "viewport-captures-and-route-smoke",
            "base_url": BASE,
            "fixture": "PostgreSQL descartável; registros sintéticos persistidos para QA visual",
            "viewports": manifest["viewports"],
            "captures": records,
            "failures": failures,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (ROOT_OUTPUT / "functional-manifest.json").write_text(
        json.dumps({
            "kind": "browser-route-smoke",
            "scope": "16 rotas autorizadas; URL, título, overflow horizontal, erros JS; agenda com alternância de visualização; paginação server-side da Recepção; alinhamento dos filtros de especialidades",
            "status": "PASS" if not failures else "FAIL",
            "checks": records,
            "failures": failures,
            "note": "Este manifesto não substitui pytest nem os fluxos completos de Playwright.",
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    passed = sum(item["status"] == "PASS" for item in records)
    mode = "com comparação local" if REFERENCE_AVAILABLE else "somente capturas; referências locais ausentes"
    print(f"Capturas operacionais: {passed}/{len(records)} PASS ({mode}); artefatos em {ROOT_OUTPUT}")
    if failures:
        print("Falhas detalhadas por rota e viewport:")
        for failure in failures:
            print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        raise AssertionError(f"Falhas de QA visual/interativo: {len(failures)}")


if __name__ == "__main__":
    main()
