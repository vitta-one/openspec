"""State-level security checks for direct prescription-print navigation.

These tests invoke Reflex event functions with route parameters and do not
substitute for browser/HTTP E2E checks documented in the manual QA protocol.
"""

import asyncio
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vitta_one.auth.authorization import AuthenticationRequiredError
from vitta_one.clinical_prescription.service import PrescriptionAuthorizationError
from vitta_one.clinical_prescription import state as prescription_state
from vitta_one.clinical_prescription.state import PrintPrescriptionState


class _PrintStateDouble:
    def __init__(self, token: str, route_id: str):
        self.token = token
        self.router = SimpleNamespace(
            page=SimpleNamespace(params={"prescription_id": route_id})
        )
        self.is_loading = False
        self.loaded = True
        self.error_message = ""
        self.patient_name = "SENTINEL: paciente antigo"
        self.professional_name = "SENTINEL"
        self.items = [{"medication_or_item": "SENTINEL"}]
        self.loaded_prescription_id = 99
        self.scheduled_at = ""
        self.registration_identifier = ""
        self.general_notes = ""

    def _clear(self):
        PrintPrescriptionState._clear(self)

    async def get_state(self, _state_class):
        return SimpleNamespace(session_token=self.token)


async def _collect(event_gen):
    results = []
    async for event in event_gen:
        results.append(event)
    return results


@pytest.mark.parametrize(
    ("token", "error", "target"),
    [
        ("doctor-b-token", PrescriptionAuthorizationError("Outro médico"), "/acesso-negado"),
        ("", AuthenticationRequiredError("Sessão ausente"), "/login"),
    ],
)
def test_direct_prescription_route_rejects_other_doctor_or_missing_session(
    monkeypatch: pytest.MonkeyPatch,
    token: str,
    error: Exception,
    target: str,
) -> None:
    """15.9/15.10: server-side route load clears data on rejected access."""
    fake = _PrintStateDouble(token=token, route_id="77")
    called = []

    def unauthorized(db, *, token, prescription_id):
        called.append((token, prescription_id))
        raise error

    monkeypatch.setattr(prescription_state, "doctor_get_printable_prescription", unauthorized)
    monkeypatch.setattr(prescription_state.rx, "session", lambda: nullcontext(object()))
    monkeypatch.setattr(prescription_state.rx, "redirect", lambda url: url)

    events = asyncio.run(_collect(PrintPrescriptionState.load.fn(fake)))

    assert called == [(token, 77)]
    assert target in events
    assert fake.loaded is False
    assert fake.patient_name == ""
    assert fake.professional_name == ""
    assert fake.items == []
    assert fake.loaded_prescription_id == 0
    assert fake.is_loading is False


def test_prescription_route_rejects_non_numeric_identifier_without_db_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct route ID must not be trusted or converted into a patient identifier."""
    fake = _PrintStateDouble(token="doctor-token", route_id="123-CPF")
    lookup = Mock(side_effect=AssertionError("Must not query invalid route"))
    monkeypatch.setattr(prescription_state, "doctor_get_printable_prescription", lookup)

    asyncio.run(_collect(PrintPrescriptionState.load.fn(fake)))

    lookup.assert_not_called()
    assert fake.loaded is False
    assert fake.patient_name == ""
    assert fake.items == []
    assert fake.loaded_prescription_id == 0
def test_logout_clears_doctor_and_print_payloads_and_removes_session_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """15.11: a successful logout clears all sensitive sibling state projections."""
    from vitta_one.admin_preview.state import AdminPreviewState
    from vitta_one.auth import state as auth_state
    from vitta_one.auth.state import AuthState
    from vitta_one.doctor_workspace.state import DoctorWorkspaceState
    from vitta_one.patient_portal.state import PatientPortalState
    from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState

    cleared = []

    class _Sibling:
        def __init__(self, name):
            self.name = name

        def _clear_active(self):
            cleared.append(self.name)

        def _clear(self):
            cleared.append(self.name)

        def _clear_sensitive_view(self):
            cleared.append(self.name)

    siblings = {
        ReceptionQueueState: _Sibling("reception"),
        DoctorQueueState: _Sibling("doctor"),
        DoctorWorkspaceState: _Sibling("doctor-workspace"),
        PatientPortalState: _Sibling("patient"),
        PrintPrescriptionState: _Sibling("print"),
        AdminPreviewState: _Sibling("admin"),
    }

    class _AuthDouble:
        session_token = "valid-test-session"
        shell_error = "previous error"
        auth_checked = False

        async def get_state(self, target):
            return siblings[target]

        async def _clear_sensitive_states(self):
            queue = await self.get_state(ReceptionQueueState)
            queue._clear_sensitive_view()
            doctor = await self.get_state(DoctorQueueState)
            doctor._clear_active()
            workspace = await self.get_state(DoctorWorkspaceState)
            workspace._clear()
            patient = await self.get_state(PatientPortalState)
            patient._clear()
            patient.error_message = ""
            print_state = await self.get_state(PrintPrescriptionState)
            print_state._clear()
            admin = await self.get_state(AdminPreviewState)
            admin._clear()

        def _clear_identity(self):
            cleared.append("identity")

    fake = _AuthDouble()
    revoked = []
    monkeypatch.setattr(auth_state.rx, "session", lambda: nullcontext(object()))
    monkeypatch.setattr(auth_state, "revoke_session", lambda db, token: revoked.append(token))
    monkeypatch.setattr(auth_state.rx, "remove_cookie", lambda name: ("cookie", name))
    monkeypatch.setattr(auth_state.rx, "redirect", lambda path: ("redirect", path))

    events = asyncio.run(_collect(AuthState.logout.fn(fake)))

    assert revoked == ["valid-test-session"]
    assert cleared == [
        "reception", "doctor", "doctor-workspace", "patient", "print", "admin", "identity"
    ]
    assert fake.session_token == ""
    assert fake.auth_checked is True
    assert ("redirect", "/login") in events
    assert any(isinstance(event, tuple) and event[0] == "cookie" for event in events)



def test_print_document_render_contract_includes_required_labels_and_unsigned_notice() -> None:
    """17.11/17.12: verify the actual Reflex document component tree, not only the constant."""
    from vitta_one.ui.prescription_components import (
        NO_DIGITAL_SIGNATURE_NOTICE,
        _print_document,
    )

    # Reflex's Tag representation includes text nodes/vars in the component tree.
    rendered = str(_print_document().render()).replace(r"\\u", r"\u")
    for label in (
        "PRESCRIÇÃO",
        "Paciente",
        "Atendimento",
        "Profissional",
        "Itens prescritos",
        "Observações gerais",
        NO_DIGITAL_SIGNATURE_NOTICE,
    ):
        escaped = "".join(
            f"\\u{ord(char):04x}" if ord(char) > 127 else char
            for char in label
        )
        assert label in rendered or escaped.lower() in rendered.lower(), (
            f"Missing required print document element: {label}"
        )
    assert "vitta-print-document" in rendered



def test_print_route_state_does_not_copy_cpf_or_put_it_in_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """15.12: even a DTO with CPF must not propagate it to the print route/state."""
    from datetime import datetime, timezone

    secret_cpf = "12345678909"
    state = _PrintStateDouble(token="doctor-author", route_id="77")
    source_view = SimpleNamespace(
        cpf=secret_cpf,
        patient_name="Pessoa de teste",
        professional_name="Dra. Exemplo",
        registration_identifier="CRM-TEST",
        scheduled_at=datetime(2026, 10, 2, 12, tzinfo=timezone.utc),
        prescription=SimpleNamespace(
            general_notes="Observações fictícias",
            items=[
                SimpleNamespace(
                    medication_or_item="Item fictício",
                    instructions="Orientação fictícia",
                    notes="",
                )
            ],
        ),
    )
    captured_ids = []

    def load_prescription(db, *, token, prescription_id):
        captured_ids.append(prescription_id)
        assert token == "doctor-author"
        return source_view

    monkeypatch.setattr(prescription_state, "doctor_get_printable_prescription", load_prescription)
    monkeypatch.setattr(prescription_state, "get_signature", lambda db, *, prescription_id: None)
    monkeypatch.setattr(prescription_state.rx, "session", lambda: nullcontext(object()))
    asyncio.run(_collect(PrintPrescriptionState.load.fn(state)))
    assert state.loaded is True
    assert state.patient_name == "Pessoa de teste"
    assert state.loaded_prescription_id == 77
    assert captured_ids == [77]
    assert state.router.page.params == {"prescription_id": "77"}
    assert secret_cpf not in repr(vars(state))
    assert all("cpf" not in key.lower() for key in vars(state))

