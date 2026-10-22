"""Route guards for task-based Administration workspaces.

New pages must be represented in the server-side route-role map, or the
authentication state rejects navigation even for valid Administrators.
"""

import pytest

from vitta_one.auth.authorization import RoleForbiddenError
from vitta_one.auth.roles import Role
from vitta_one.auth.state import _ADMIN_PREVIEW_ROUTES, _ROLE_BY_ROUTE


_ADMIN_TASK_ROUTES = (
    "/admin",
    "/admin/funcionarios",
    "/admin/funcionarios/novo",
    "/admin/funcionarios/[employee_id]",
    "/admin/funcionarios/medico",
    "/admin/funcionarios/recepcionista",
    "/admin/horarios",
    "/admin/configuracoes",
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
