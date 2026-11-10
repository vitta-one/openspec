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
    state.prescriptions = [{"id": 7, "items": [{"medication_or_item": "Segredo"}]}]
    state.new_prescription_dialog_open = True
    state.new_prescription_medication = "Segredo"
    state.new_prescription_instructions = "Segredo"
    state.new_prescription_item_notes = "Segredo"
    state.new_prescription_general_notes = "Segredo"
    state.prescription_item_dialog_open = True
    state.prescription_item_mode = "edit"
    state.prescription_target_id = 7
    state.prescription_item_id = 8
    state.prescription_item_medication = "Segredo"
    state.prescription_item_instructions = "Segredo"
    state.prescription_item_notes = "Segredo"
    state.prescription_notes_dialog_open = True
    state.prescription_notes_target_id = 7
    state.prescription_general_notes = "Segredo"
    state.delete_prescription_dialog_open = True
    state.delete_prescription_id = 7
    state.remove_prescription_item_dialog_open = True
    state.remove_prescription_id = 7
    state.remove_prescription_item_id = 8
    state.remove_prescription_item_name = "Segredo"
    state.is_prescription_submitting = True
    state.clinical_attachments = [{"id": 9, "title": "Documento sensível"}]
    state.attachment_title = "Documento sensível"
    state.attachment_category = "EXAME"
    state.attachment_exam_date = "2026-11-10"
    state.is_attachment_submitting = True
    state.attachment_delete_dialog_open = True
    state.attachment_delete_id = 9
    state.attachment_delete_title = "Documento sensível"
    state._reset_new_prescription = MethodType(DoctorQueueState._reset_new_prescription, state)
    state._reset_prescription_item_dialog = MethodType(DoctorQueueState._reset_prescription_item_dialog, state)
    state._reset_prescription_notes_dialog = MethodType(DoctorQueueState._reset_prescription_notes_dialog, state)
    state._reset_delete_prescription = MethodType(DoctorQueueState._reset_delete_prescription, state)
    state._reset_remove_item = MethodType(DoctorQueueState._reset_remove_item, state)
    state._clear_prescriptions = MethodType(DoctorQueueState._clear_prescriptions, state)
    state._clear_attachments = MethodType(DoctorQueueState._clear_attachments, state)
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
    assert state.prescriptions == []
    assert state.new_prescription_dialog_open is False
    assert state.new_prescription_medication == ""
    assert state.prescription_item_dialog_open is False
    assert state.prescription_item_medication == ""
    assert state.prescription_notes_dialog_open is False
    assert state.prescription_general_notes == ""
    assert state.delete_prescription_dialog_open is False
    assert state.remove_prescription_item_dialog_open is False
    assert state.remove_prescription_item_name == ""
    assert state.is_prescription_submitting is False
    assert state.clinical_attachments == []
    assert state.attachment_title == ""
    assert state.attachment_exam_date == ""
    assert state.is_attachment_submitting is False
    assert state.attachment_delete_dialog_open is False

