"""Read-only structural guard for the public queue-first emergency-care navigation.

This test intentionally does not assert clinical migration acceptance. Clinical
care for walk-ins requires the separate transactional migration in the change.
"""
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    return next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name)


def _calls(module_text: str) -> list[ast.Call]:
    return [node for node in ast.walk(ast.parse(module_text)) if isinstance(node, ast.Call)]


def test_appointment_routes_are_not_published():
    calls = [
        call for call in _calls(_source("vitta_one/vitta_one.py"))
        if isinstance(call.func, ast.Attribute)
        and call.func.attr == "add_page"
    ]
    paths = {
        kw.value.value
        for call in calls
        for kw in call.keywords
        if kw.arg == "route" and isinstance(kw.value, ast.Constant)
    }
    assert not paths.intersection(
        {"/recepcao/agenda", "/medico/agenda", "/admin/agenda", "/medico/pacientes"}
    )


def test_reception_home_renders_real_queue_instead_of_daily_appointments():
    source = _source("vitta_one/ui/pages.py")
    node = _function(ast.parse(source), "reception_page")
    call_names = {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    assert "active_queue_panel" in call_names
    assert "reception_dashboard" not in call_names


def test_navigation_does_not_offer_scheduling():
    source = _source("vitta_one/ui/components.py")
    tree = ast.parse(source)
    nav = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_NAV_BY_ROLE" for t in node.targets)
    )
    labels = [
        literal.value
        for literal in ast.walk(nav.value)
        if isinstance(literal, ast.Constant) and isinstance(literal.value, str)
    ]
    assert "Agenda" not in labels
    assert "Minhas consultas" not in labels
    assert "Meus atendimentos" in labels


def test_patient_portal_does_not_claim_a_scheduling_calendar():
    node = _function(ast.parse(_source("vitta_one/ui/pages.py")), "patient_portal_page")
    call_names = {
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    assert not call_names.intersection({"patient_calendar", "patient_consultation_list"})
