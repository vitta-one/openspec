"""Guarda documental de estrutura e cenários das specs canônicas OpenSpec.

Os testes não substituem o validador strict oficial, nem exercitam Reflex ou
integrações externas. Eles impedem regressões triviais na cobertura do catálogo.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "openspec" / "specs"
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


def test_expected_capabilities_have_canonical_spec() -> None:
    found = {path.parent.name for path in SPECS.glob("*/spec.md")}
    assert EXPECTED <= found, sorted(EXPECTED - found)


def test_canonical_specs_contain_verifiable_scenarios() -> None:
    for path in sorted(SPECS.glob("*/spec.md")):
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
    auth = (SPECS / "access-control" / "spec.md").read_text(encoding="utf-8")
    care = (SPECS / "clinical-care-record" / "spec.md").read_text(encoding="utf-8")
    assert "e Paciente" in config
    assert "role PACIENTE" in auth
    assert "Walk-in permanece sem registro" not in care
    assert "QueueEntry" in care


def test_future_integrations_remain_in_changes() -> None:
    assert not (SPECS / "examination-management" / "spec.md").exists()
    assert not (SPECS / "prescription-signature" / "spec.md").exists()
    for change, capability in (
        ("add-examination-attachments", "examination-management"),
        ("add-prescription-signature", "prescription-signature"),
    ):
        root = CHANGES / change
        for artifact in ("proposal.md", "design.md", "tasks.md"):
            assert (root / artifact).exists(), f"{change}/{artifact}"
        assert (root / "specs" / capability / "spec.md").exists()
        assert "- [ ]" in (root / "tasks.md").read_text(encoding="utf-8")
