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
