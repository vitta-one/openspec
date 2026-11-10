"""Signature state, immutability, webhook ordering and resource ownership."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.roles import Role
from vitta_one.clinical_prescription.service import PrescriptionTransitionError, update_prescription_notes
from vitta_one.digital_signature.service import (
    SignatureAuthorizationError, process_zapsign_webhook, signed_document_url,
)
from vitta_one.integrations.zapsign import ZapSignDocument
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.clinical_prescription import Prescription, PrescriptionItem
from vitta_one.models.digital_signature import PrescriptionSignatureRequest
from vitta_one.models.patient_queue import Patient, QueueEntry
from vitta_one.models.professional import Professional


class FakeZapSign:
    def get_document(self, token: str) -> ZapSignDocument:
        return ZapSignDocument(token, "signed", "signer", "https://temporary.example/signed.pdf")


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def zapsign_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZAPSIGN_API_TOKEN", "api")
    monkeypatch.setenv("ZAPSIGN_WEBHOOK_TOKEN", "webhook")


def _context(db: Session):
    doctor = User(email="doctor-signature@example.com", display_name="Dra. Assinatura", password_hash="hash", role=Role.MEDICO.value)
    patient_user = User(email="patient-signature@example.com", password_hash="hash", role=Role.PACIENTE.value)
    db.add(doctor)
    db.add(patient_user)
    db.flush()
    db.add(Professional(name="Dra. Assinatura", registration_identifier="CRM-SIGN", user_id=doctor.id))
    patient = Patient(name="Paciente Assinatura", cpf="12345678901", user_id=patient_user.id)
    db.add(patient)
    db.flush()
    entry = QueueEntry(
        patient_id=patient.id, symptoms="Teste", priority="VERDE", status="EM_ATENDIMENTO",
        doctor_user_id=doctor.id, entered_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()
    record = ClinicalCareRecord(queue_entry_id=entry.id, patient_id=patient.id, doctor_user_id=doctor.id)
    db.add(record)
    db.flush()
    prescription = Prescription(clinical_care_record_id=record.id, consultation_id=None, doctor_user_id=doctor.id)
    db.add(prescription)
    db.flush()
    db.add(PrescriptionItem(prescription_id=prescription.id, medication_or_item="Item", instructions="Usar conforme orientação"))
    request = PrescriptionSignatureRequest(
        prescription_id=prescription.id, requested_by_user_id=doctor.id,
        request_key="a" * 64, external_id="vitta-prescription-test",
        provider_document_token="doc-test", signer_email=doctor.email, status="PENDING",
    )
    db.add(request)
    db.commit()
    for row in (doctor, patient_user, prescription, request):
        db.refresh(row)
    return doctor, patient_user, prescription, request


def test_sent_prescription_is_immutable(db: Session) -> None:
    doctor, _, prescription, _ = _context(db)
    with pytest.raises(PrescriptionTransitionError, match="envio para assinatura"):
        update_prescription_notes(
            db, prescription_id=prescription.id, doctor_user_id=doctor.id,
            general_notes="Não deve alterar",
        )


def test_signature_webhook_is_idempotent_and_terminal_state_does_not_regress(db: Session) -> None:
    _, _, _, request = _context(db)
    signed = {
        "event_id": "evt-signed", "event_type": "doc_signed", "token": "doc-test",
        "status": "signed", "last_update_at": "2026-11-10T12:00:00Z",
    }
    assert process_zapsign_webhook(db, signed) == "PROCESSED"
    assert process_zapsign_webhook(db, signed) == "DUPLICATE"
    stale = {
        "event_id": "evt-created-late", "event_type": "doc_created", "token": "doc-test",
        "status": "pending", "last_update_at": "2026-11-10T11:00:00Z",
    }
    assert process_zapsign_webhook(db, stale) == "STALE"
    assert db.get(PrescriptionSignatureRequest, request.id).status == "SIGNED"


def test_signed_document_access_is_scoped_to_owner(db: Session) -> None:
    doctor, patient_user, prescription, request = _context(db)
    request.status = "SIGNED"
    db.add(request)
    db.commit()
    assert signed_document_url(
        db, prescription_id=prescription.id, actor_user_id=doctor.id,
        actor_is_patient=False, client=FakeZapSign(),
    ).endswith("signed.pdf")
    assert signed_document_url(
        db, prescription_id=prescription.id, actor_user_id=patient_user.id,
        actor_is_patient=True, client=FakeZapSign(),
    ).endswith("signed.pdf")

    outsider = User(email="other-doctor@example.com", password_hash="hash", role=Role.MEDICO.value)
    db.add(outsider)
    db.commit()
    with pytest.raises(SignatureAuthorizationError):
        signed_document_url(
            db, prescription_id=prescription.id, actor_user_id=outsider.id,
            actor_is_patient=False, client=FakeZapSign(),
        )
