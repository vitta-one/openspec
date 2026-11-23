"""Guarda documental da estrutura e cenários do snapshot OpenSpec.

Os testes não substituem o validador strict oficial, nem exercitam Reflex ou
integrações externas. Eles impedem regressões triviais na cobertura do catálogo.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "openspec" / "specs"
ARCHIVED_SPECS = ROOT / "docs" / "archive" / "openspec-specs-2026-11-22"
CHANGES = ROOT / "openspec" / "changes"

EXPECTED = {
    "access-control",
    "admin-qa-patient-dossier",
    "administration-dashboard",
    "appointment-email-notifications",
    "appointment-scheduling",
    "asaas-payments",
    "clinic-settings",
    "clinical-care-record",
    "clinical-prescription",
    "consultation-care-lifecycle",
    "doctor-workspace",
    "email-delivery",
    "emergency-queue-clinical-care",
    "financial-management",
    "operational-screen-presentation",
    "patient-directory",
    "patient-portal",
    "patient-reception-queue",
    "patient-self-booking",
    "payment-notifications",
    "professional-specialty-management",
    "professional-working-hours",
    "reception-operational-dashboard",
    "staff-management",
    "transactional-email",
}


def test_expected_capabilities_are_archived() -> None:
    found = {path.parent.name for path in ARCHIVED_SPECS.glob("*/spec.md")}
    assert found == EXPECTED, sorted(EXPECTED ^ found)


def test_active_specs_are_empty() -> None:
    assert SPECS.is_dir()
    assert {path.name for path in SPECS.iterdir()} == {".gitkeep"}


def test_archived_specs_contain_verifiable_scenarios() -> None:
    for path in sorted(ARCHIVED_SPECS.glob("*/spec.md")):
        source = path.read_text(encoding="utf-8")
        name = path.parent.name
        assert source.startswith(f"# {name} Specification"), name
        assert "## Purpose" in source and "## Requirements" in source, name
        assert not re.search(r"(?m)^## (?:ADDED|MODIFIED|REMOVED) Requirements", source), name

        headings = list(re.finditer(r"(?m)^### Requirement: (.+)$", source))
        assert headings, f"{name}: missing requirements"
        names = [m.group(1) for m in headings]
        assert len(set(names)) == len(names), f"{name}: duplicate requirements"

        for index, heading in enumerate(headings):
            block = source[heading.end():headings[index + 1].start() if index + 1 < len(headings) else None]
            requirement_text = block.split("#### Scenario:", 1)[0]
            assert re.search(r"\b(?:MUST|SHALL)\b", requirement_text), f"{name}: {heading.group(1)}"
            scenarios = list(re.finditer(r"(?m)^#### Scenario: (.+)$", block))
            assert scenarios, f"{name}: no scenarios for {heading.group(1)}"
            scenario_names = [m.group(1) for m in scenarios]
            assert len(scenario_names) == len(set(scenario_names)), f"{name}: duplicate scenarios"
            for number, scenario in enumerate(scenarios):
                body = block[scenario.end():scenarios[number + 1].start() if number + 1 < len(scenarios) else None]
                assert "**WHEN**" in body and "**THEN**" in body, f"{name}: {scenario.group(1)}"


def test_patient_role_and_walkin_are_consistent() -> None:
    config = (ROOT / "openspec" / "config.yaml").read_text(encoding="utf-8")
    auth = (ARCHIVED_SPECS / "access-control" / "spec.md").read_text(encoding="utf-8")
    care = (ARCHIVED_SPECS / "clinical-care-record" / "spec.md").read_text(encoding="utf-8")
    assert "e Paciente" in config
    assert "role PACIENTE" in auth
    assert "Walk-in permanece sem registro" not in care
    assert "QueueEntry" in care


def test_reconciled_changes_are_archived() -> None:
    """As changes existentes no corte acadêmico seguem rastreáveis no histórico.

    Não proíbe criação de novas changes pelo fluxo normal do OpenSpec.
    """
    names = {
        "2026-10-31-admin-qa-patient-dossier",
        "2026-10-31-fix-professional-registration-modal",
        "2026-10-31-manage-clinic-configuration",
        "2026-10-31-reception-booking-modal",
        "2026-10-31-refine-admin-hub-navigation",
        "2026-10-31-refine-employee-detail",
        "2026-10-31-refine-employee-directory",
        "2026-10-31-refine-reception-agenda-checkin",
        "2026-10-31-refine-specialty-management",
        "2026-10-31-separate-patient-registration-portal",
        "2026-10-31-unify-staff-registration",
        "admin-horarios-calendario-operacional",
        "admin-qa-agenda-visual",
        "align-16-operational-screen-visual-parity",
        "align-operational-screen-visual-parity",
        "extend-resend-email",
        "integrate-asaas-financial",
        "reception-operacao-do-dia-20261031",
        "reception-patient-directory-20261031",
        "reception-patient-operational-profile",
        "reception-patient-registration-ux",
        "reception-queue-operational-board-20261031",
        "refactor-admin-profissionais-20261031",
        "refinar-modais-especialidades-20261031",
        "refine-admin-reception-qa-panel",
        "refine-global-navigation-20261031",
    }
    for name in names:
        archive_name = name if name[:4].isdigit() and name[4] == "-" else f"2026-11-22-{name}"
        destination = CHANGES / "archive" / archive_name
        assert destination.is_dir(), f"Archive ausente: {archive_name}"
        assert (destination / "proposal.md").is_file(), archive_name
        assert not (CHANGES / name).exists(), f"Change ainda ativa: {name}"
