"""Sensitive-state cleanup coverage for the doctor clinical workspace."""

from types import MethodType

from vitta_one.patient_queue.state import DoctorQueueState


class _DummyDoctorState:
    pass


def test_clear_active_removes_clinical_form_and_history() -> None:
    state = _DummyDoctorState()
    state.has_active = True
    state.active_entry_id = 44
    state.active_consultation_id = 12
    state.active_patient_name = "Paciente sensível"
    state.active_symptoms = "Relato"
    state.active_priority = "VERDE"
    state.active_priority_label = "Verde"
    state.active_called_at = "10:00"
    state.active_is_scheduled = True
    state.active_scheduled_at = "02/10/2026 às 10:00"
    state.active_professional_name = "Dra. Teste"
    state.clinical_record_id = 99
    state.clinical_chief_complaint = "Conteúdo clínico"
    state.clinical_anamnesis = "Conteúdo clínico"
    state.clinical_diagnosis = "Conteúdo clínico"
    state.clinical_conduct_notes = "Conteúdo clínico"
    state.persisted_chief_complaint = "Conteúdo clínico"
    state.persisted_anamnesis = "Conteúdo clínico"
    state.persisted_diagnosis = "Conteúdo clínico"
    state.persisted_conduct_notes = "Conteúdo clínico"
    state.clinical_history = [{"diagnosis": "Histórico"}]
    state.clinical_history_page = 2
    state.clinical_history_total_pages = 3
    state.clinical_history_total_count = 25
    state._clear_clinical = MethodType(DoctorQueueState._clear_clinical, state)

    DoctorQueueState._clear_active(state)

    assert state.has_active is False
    assert state.active_entry_id == 0
    assert state.active_consultation_id == 0
    assert state.active_patient_name == ""
    assert state.clinical_record_id == 0
    assert state.clinical_chief_complaint == ""
    assert state.clinical_anamnesis == ""
    assert state.clinical_diagnosis == ""
    assert state.clinical_conduct_notes == ""
    assert state.clinical_history == []
    assert state.clinical_history_page == 1
    assert state.clinical_history_total_count == 0
