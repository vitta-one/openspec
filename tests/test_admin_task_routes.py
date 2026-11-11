"""Route guards for task-based Administration workspaces.

New pages must be represented in the server-side route-role map, or the
authentication state rejects navigation even for valid Administrators.
"""

import pytest

from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.state import _ADMIN_PREVIEW_ROUTES, _ROLE_BY_ROUTE
from vitta_one.ui.components import _ADMIN_PREVIEW_NAV, _ADMIN_TASK_NAV


_ADMIN_TASK_ROUTES = (
    "/admin",
    "/admin/funcionarios",
    "/admin/funcionarios/novo",
    "/admin/funcionarios/[employee_id]",
    "/admin/funcionarios/medico",
    "/admin/funcionarios/recepcionista",
    "/admin/horarios",
    "/admin/configuracoes",
    "/admin/financeiro",
    "/admin/especialidades",
    "/admin/profissionais",
)


@pytest.mark.parametrize("route", _ADMIN_TASK_ROUTES)
def test_admin_task_route_has_server_side_role_guard(route: str) -> None:
    assert _ROLE_BY_ROUTE.get(route) is Role.ADMINISTRADOR


@pytest.mark.parametrize("route", _ADMIN_TASK_ROUTES)
def test_admin_task_routes_are_not_qa_only_previews(route: str) -> None:
    assert route not in _ADMIN_PREVIEW_ROUTES


def test_unregistered_admin_route_is_not_implicitly_authorized() -> None:
    assert _ROLE_BY_ROUTE.get("/admin/rota-inexistente") is None


@pytest.mark.parametrize("route", (
    "/recepcao/pacientes", "/recepcao/pacientes/novo",
    "/recepcao/pacientes/[patient_id]",
))
def test_patient_registration_and_details_require_receptionist_role(route: str) -> None:
    assert _ROLE_BY_ROUTE.get(route) is Role.RECEPCIONISTA


def test_medical_records_are_not_an_unprotected_route() -> None:
    assert _ROLE_BY_ROUTE.get("/medico/prontuarios") is Role.MEDICO


@pytest.mark.parametrize("label, route, icon, active_key", _ADMIN_TASK_NAV)
def test_admin_sidebar_destinations_are_real_authorized_routes(
    label: str, route: str, icon: str, active_key: str,
) -> None:
    assert label and icon and active_key
    assert route in _ADMIN_TASK_ROUTES
    assert _ROLE_BY_ROUTE[route] is Role.ADMINISTRADOR
    assert route not in _ADMIN_PREVIEW_ROUTES


def test_admin_qa_links_are_separate_from_real_administration() -> None:
    task_routes = {href for _, href, _, _ in _ADMIN_TASK_NAV}
    preview_routes = {href for _, href, _, _ in _ADMIN_PREVIEW_NAV}
    assert len(task_routes) == len(_ADMIN_TASK_NAV)
    assert len(preview_routes) == len(_ADMIN_PREVIEW_NAV)
    # Contextual detail routes are QA-only, but must not clutter the sidebar.
    assert preview_routes.issubset(_ADMIN_PREVIEW_ROUTES)
    assert _ADMIN_PREVIEW_ROUTES - preview_routes == {"/admin/pacientes/[patient_id]"}
    assert task_routes.isdisjoint(_ADMIN_PREVIEW_ROUTES)


def test_admin_patient_detail_is_qa_protected_without_sidebar_duplicate() -> None:
    assert "/admin/pacientes/[patient_id]" in _ADMIN_PREVIEW_ROUTES
    assert "/admin/pacientes/[patient_id]" not in {
        href for _, href, _, _ in _ADMIN_PREVIEW_NAV
    }
    assert "/admin/pacientes/[patient_id]" not in _ROLE_BY_ROUTE


def test_admin_sidebar_has_explicit_active_key_for_each_destination() -> None:
    keys = [active for _, _, _, active in _ADMIN_TASK_NAV]
    assert len(keys) == len(set(keys))
    assert "administracao" in keys
