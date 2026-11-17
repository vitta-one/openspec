"""State-level security checks for direct prescription-print navigation.

These tests invoke Reflex event functions with route parameters and do not
substitute for browser/HTTP E2E checks documented in the manual QA protocol.
"""

import asyncio
from contextlib import nullcontext
from types import MethodType, SimpleNamespace
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
    """Logout and session expiry clear all sensitive sibling state projections."""
    from vitta_one.admin_preview.state import AdminPreviewState
    from vitta_one.admin_preview.agenda_state import AdminAgendaPreviewState
    from vitta_one.admin_preview.reception_state import AdminReceptionPreviewState
    from vitta_one.admin_dashboard.state import AdminDashboardState
    from vitta_one.appointment_scheduling.state import (
        AdminAvailabilityState, ReceptionAgendaState,
    )
    from vitta_one.auth import state as auth_state
    from vitta_one.auth.staff_state import AdminStaffState
    from vitta_one.auth.state import AuthState
    from vitta_one.doctor_workspace.state import DoctorWorkspaceState
    from vitta_one.financial.state import FinancialState
    from vitta_one.notifications.operations import EmailOperationsState
    from vitta_one.notifications.state import NotificationState
    from vitta_one.patient_portal.state import (
        AdminClinicConfigurationState, PatientPortalState,
    )
    from vitta_one.patient_portal.booking_state import PatientBookingState
    from vitta_one.patient_queue.state import DoctorQueueState, ReceptionQueueState
    from vitta_one.professional_directory.state import AdminDirectoryState
    from vitta_one.reception.dashboard.state import ReceptionDashboardState
    from vitta_one.ui.components import SidebarState

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

        def _clear_data(self):
            cleared.append(self.name)

        def _reset_selection(self):
            cleared.append(self.name)

    dashboard = SimpleNamespace(
        appointments=[{"patient_name": "SENTINEL: paciente da recepção"}],
        upcoming_appointments=[{"patient_name": "SENTINEL: próximo atendimento"}],
    )

    def _clear_dashboard_details():
        ReceptionDashboardState._clear_details(dashboard)

    def _clear_dashboard_data():
        ReceptionDashboardState._clear_data(dashboard)
        cleared.append("reception-dashboard")

    dashboard._clear_details = _clear_dashboard_details
    dashboard._clear_data = _clear_dashboard_data

    def _action_state(method_name, label, action):
        def run():
            action()
            cleared.append(label)

        return SimpleNamespace(**{method_name: run})

    agenda = SimpleNamespace(
        professionals=[{"label": "SENTINEL médico"}],
        slots=[{"professional_name": "SENTINEL médico"}],
        consultations=[{"patient_name": "SENTINEL paciente"}],
        patient_cpf="SENTINEL CPF",
        selected_patient_id=81,
        selected_patient_name="SENTINEL paciente",
        error_message="error",
        success_message="success",
    )
    for name in (
        "_reset_booking", "_reset_arrival", "_reset_reschedule", "_reset_cancel",
        "_clear_feedback",
    ):
        setattr(agenda, name, MethodType(getattr(ReceptionAgendaState, name), agenda))
    staff = SimpleNamespace(
        emails=["staff@example.invalid"],
        employees=[{"email": "staff@example.invalid", "name": "SENTINEL"}],
        employee_detail={"email": "staff@example.invalid"},
        new_name="SENTINEL", new_email="staff@example.invalid",
    )
    directory = SimpleNamespace(
        specialties=[],
        professionals=[{"user_email": "doctor@example.invalid"}],
        recent_professionals=[{"user_email": "doctor@example.invalid"}],
        medical_accounts=[{"email": "doctor@example.invalid"}],
        professional_search="doctor@example.invalid",
        professional_email="doctor@example.invalid",
        status_professional_name="SENTINEL médico",
    )
    for name in (
        "_reset_specialty_status_change", "_reset_specialty_edit",
        "_reset_professional_form", "_clear_feedback",
    ):
        setattr(directory, name, MethodType(getattr(AdminDirectoryState, name), directory))
    admin_agenda_preview = SimpleNamespace(
        professionals=[{"label": "SENTINEL médico"}],
        day_slots=[{"professional_name": "SENTINEL médico"}],
        day_consultations=[{"professional_name": "SENTINEL médico"}],
    )
    admin_agenda_preview._clear_results = MethodType(
        AdminAgendaPreviewState._clear_results, admin_agenda_preview
    )
    availability = SimpleNamespace(
        professionals=[{"label": "SENTINEL médico"}],
        slots=[{"professional_name": "SENTINEL médico"}],
        weekly_saved_summary="SENTINEL expediente",
        error_message="error", success_message="success",
    )
    availability._clear_feedback = MethodType(
        AdminAvailabilityState._clear_feedback, availability
    )
    admin_dashboard = SimpleNamespace(consultations_today=12, error_message="error")
    clinic_configuration = SimpleNamespace(
        clinic_name="SENTINEL clínica", clinic_address="SENTINEL endereço",
    )

    siblings = {
        ReceptionQueueState: _Sibling("reception"),
        ReceptionAgendaState: _action_state(
            "_clear_sensitive", "agenda",
            lambda: ReceptionAgendaState._clear_sensitive(agenda),
        ),
        AdminStaffState: _action_state(
            "_clear_sensitive_data", "staff",
            lambda: AdminStaffState._clear_sensitive_data(staff),
        ),
        AdminDirectoryState: _action_state(
            "_clear_sensitive_data", "directory",
            lambda: AdminDirectoryState._clear_sensitive_data(directory),
        ),
        AdminAgendaPreviewState: _action_state(
            "_clear_sensitive_data", "admin-agenda-preview",
            lambda: AdminAgendaPreviewState._clear_sensitive_data(admin_agenda_preview),
        ),
        AdminAvailabilityState: _action_state(
            "_clear_sensitive", "admin-availability",
            lambda: AdminAvailabilityState._clear_sensitive(availability),
        ),
        AdminDashboardState: _action_state(
            "_clear", "admin-dashboard", lambda: AdminDashboardState._clear(admin_dashboard),
        ),
        AdminClinicConfigurationState: _action_state(
            "_clear", "clinic-configuration",
            lambda: AdminClinicConfigurationState._clear(clinic_configuration),
        ),
        ReceptionDashboardState: dashboard,
        DoctorQueueState: _Sibling("doctor"),
        DoctorWorkspaceState: _Sibling("doctor-workspace"),
        PatientPortalState: _Sibling("patient"),
        PatientBookingState: _Sibling("booking"),
        PrintPrescriptionState: _Sibling("print"),
        AdminPreviewState: _Sibling("admin"),
        AdminReceptionPreviewState: _Sibling("admin-reception"),
        FinancialState: _Sibling("financial"),
        NotificationState: _Sibling("notification"),
        EmailOperationsState: _Sibling("email-operations"),
        SidebarState: _Sibling("sidebar"),
    }
    siblings[SidebarState].active_profile = "MEDICO"
    siblings[SidebarState].user_changed_desktop = True

    class _AuthDouble:
        session_token = "valid-test-session"
        shell_error = "previous error"
        auth_checked = False
        router = SimpleNamespace(route_id="/recepcao")

        async def get_state(self, target):
            return siblings[target]

        async def _clear_sensitive_states(self):
            await AuthState._clear_sensitive_states(self)

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
        "reception", "agenda", "staff", "directory", "admin-agenda-preview",
        "admin-availability", "admin-dashboard", "clinic-configuration",
        "reception-dashboard",
        "doctor", "doctor-workspace", "patient",
        "booking", "print", "admin", "admin-reception", "financial", "notification",
        "email-operations", "identity",
    ]
    assert agenda.professionals == []
    assert agenda.slots == []
    assert agenda.consultations == []
    assert agenda.patient_cpf == ""
    assert agenda.selected_patient_name == ""
    assert agenda.arrival_patient_name == ""
    assert agenda.arrival_symptoms == ""
    assert staff.emails == []
    assert staff.employees == []
    assert staff.employee_detail["email"] == ""
    assert staff.new_name == ""
    assert staff.new_email == ""
    assert directory.professionals == []
    assert directory.recent_professionals == []
    assert directory.medical_accounts == []
    assert directory.professional_search == ""
    assert directory.professional_email == ""
    assert directory.status_professional_name == ""
    assert admin_agenda_preview.professionals == []
    assert admin_agenda_preview.day_slots == []
    assert availability.professionals == []
    assert availability.slots == []
    assert availability.weekly_saved_summary == ""
    assert admin_dashboard.consultations_today == 0
    assert admin_dashboard.error_message == ""
    assert clinic_configuration.clinic_name == ""
    assert clinic_configuration.clinic_address == ""
    assert dashboard.appointments == []
    assert dashboard.upcoming_appointments == []
    assert dashboard.details_patient_name == ""
    assert fake.session_token == ""
    assert fake.auth_checked is True
    assert siblings[SidebarState].active_profile == ""
    assert siblings[SidebarState].user_changed_desktop is False
    assert ("redirect", "/login") in events
    assert any(isinstance(event, tuple) and event[0] == "cookie" for event in events)

    dashboard.upcoming_appointments = [{"patient_name": "SENTINEL: paciente após expiração"}]
    dashboard.details_patient_name = "SENTINEL"
    agenda.consultations = [{"patient_name": "SENTINEL após expiração"}]
    agenda.patient_cpf = "SENTINEL CPF"
    staff.employees = [{"email": "staff@example.invalid"}]
    staff.new_email = "staff@example.invalid"
    directory.professionals = [{"user_email": "doctor@example.invalid"}]
    directory.professional_email = "doctor@example.invalid"
    admin_agenda_preview.professionals = [{"label": "SENTINEL após expiração"}]
    availability.professionals = [{"label": "SENTINEL após expiração"}]
    admin_dashboard.consultations_today = 99
    clinic_configuration.clinic_address = "SENTINEL após expiração"
    fake.session_token = "expired-test-session"

    def _expired_session(*_args, **_kwargs):
        raise AuthenticationRequiredError("Sessão expirada")

    monkeypatch.setattr(auth_state, "require_role", _expired_session)
    expired_events = asyncio.run(_collect(AuthState.load_protected.fn(fake)))

    assert dashboard.upcoming_appointments == []
    assert dashboard.details_patient_name == ""
    assert agenda.consultations == []
    assert agenda.patient_cpf == ""
    assert staff.employees == []
    assert staff.new_email == ""
    assert directory.professionals == []
    assert directory.professional_email == ""
    assert admin_agenda_preview.professionals == []
    assert availability.professionals == []
    assert admin_dashboard.consultations_today == 0
    assert clinic_configuration.clinic_address == ""
    assert fake.session_token == ""
    assert ("redirect", "/login") in expired_events
    assert any(isinstance(event, tuple) and event[0] == "cookie" for event in expired_events)



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
    monkeypatch.setattr(prescription_state.rx, "session", lambda: nullcontext(object()))
    asyncio.run(_collect(PrintPrescriptionState.load.fn(state)))
    assert state.loaded is True
    assert state.patient_name == "Pessoa de teste"
    assert state.loaded_prescription_id == 77
    assert captured_ids == [77]
    assert state.router.page.params == {"prescription_id": "77"}
    assert secret_cpf not in repr(vars(state))
    assert all("cpf" not in key.lower() for key in vars(state))
