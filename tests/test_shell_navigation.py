"""Regressões do shell compartilhado: rotas autorizadas, hierarquia e montagem Reflex."""

from pathlib import Path

import pytest

from vitta_one.auth.roles import Role
from vitta_one.ui.components import (
    _ADMIN_MANAGEMENT_NAV,
    _ADMIN_PREVIEW_NAV,
    _NAV_BY_ROLE,
    _nav_link,
    _role_navigation,
    authenticated_sidebar,
    authenticated_topbar,
)


def test_admin_management_contains_only_existing_administrative_destinations() -> None:
    assert {item[1] for item in _ADMIN_MANAGEMENT_NAV} == {
        "/admin/funcionarios",
        "/admin/profissionais",
        "/admin/especialidades",
        "/admin/horarios",
        "/admin/configuracoes",
    }
    assert {item[3] for item in _ADMIN_MANAGEMENT_NAV} == {
        "funcionarios",
        "profissionais",
        "especialidades",
        "horarios",
        "configuracoes",
    }


def test_qa_preview_is_separate_from_management_and_uses_admin_prefix() -> None:
    admin_paths = {item[1] for item in _ADMIN_MANAGEMENT_NAV}
    preview_paths = {item[1] for item in _ADMIN_PREVIEW_NAV}
    assert len(preview_paths) == len(_ADMIN_PREVIEW_NAV)
    assert all(path.startswith("/admin/") for path in preview_paths)
    assert admin_paths.isdisjoint(preview_paths)
    assert "/recepcao" not in preview_paths
    assert "/medico" not in preview_paths


@pytest.mark.parametrize(
    ("role", "prefix"),
    [
        (Role.RECEPCIONISTA, "/recepcao"),
        (Role.MEDICO, "/medico"),
        (Role.PACIENTE, "/paciente"),
        (Role.FINANCEIRO, "/financeiro"),
    ],
)
def test_role_navigation_does_not_expose_other_roles(role: Role, prefix: str) -> None:
    items = _NAV_BY_ROLE[role]
    assert all(path == prefix or path.startswith(prefix + "/") for _, path, _, _ in items)
    assert len({key for _, _, _, key in items}) == len(items)


@pytest.mark.parametrize(
    ("role", "active"),
    [
        (Role.ADMINISTRADOR, "funcionarios"),
        (Role.ADMINISTRADOR, "horarios"),
        (Role.ADMINISTRADOR, "profissionais"),
        (Role.RECEPCIONISTA, "agenda"),
        (Role.MEDICO, "atendimento"),
        (Role.PACIENTE, "consultas-paciente"),
        (Role.FINANCEIRO, "financeiro"),
    ],
)
def test_shared_shell_components_mount_for_authorized_roles(role: Role, active: str) -> None:
    assert _role_navigation(role, active) is not None
    assert authenticated_sidebar(role, active) is not None
    assert authenticated_topbar(role) is not None


def test_nav_link_active_and_ancestor_variants_mount_without_second_component() -> None:
    assert _nav_link("Funcionários", "/admin/funcionarios", "users", active=True, child=True)
    assert _nav_link("Visão geral", "/admin", "layout_dashboard", active=False, ancestor=True)


def test_mobile_drawer_has_keyboard_and_scroll_recovery_contract() -> None:
    script = (Path(__file__).resolve().parents[1] / "assets" / "shell-navigation.js").read_text()
    assert 'event.key === "Escape"' in script
    assert 'event.key !== "Tab"' in script
    assert "lastMain.inert = true" in script
    assert "lastMain.inert = false" in script
    assert 'aria-modal' in script
    assert 'previousHtmlOverflow' in script
