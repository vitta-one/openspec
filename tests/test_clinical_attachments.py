"""Clinical attachment validation, authorization and provider orchestration."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from vitta_one.auth.roles import Role
from vitta_one.clinical_documents.service import (
    AttachmentAuthorizationError, AttachmentError, attachment_download_url,
    create_attachment, list_patient_attachments, remove_attachment,
    set_patient_visibility,
)
from vitta_one.integrations.cloudinary import UploadedAsset
from vitta_one.models.auth import User
from vitta_one.models.clinical_care import ClinicalCareRecord
from vitta_one.models.patient_queue import Patient, QueueEntry


class FakeCloudinary:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def upload(self, *, content: bytes, filename: str, public_id: str) -> UploadedAsset:
        return UploadedAsset("asset-1", f"vitta-one/clinical/{public_id}", 1, "raw", "pdf", len(content))

    def private_download_url(self, *, public_id: str, format: str, resource_type: str) -> str:
        return "https://api.cloudinary.com/private-temporary"

    def delete(self, *, public_id: str, resource_type: str) -> None:
        self.deleted.append(public_id)


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def cloudinary_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDINARY_CLOUD_NAME", "test")
    monkeypatch.setenv("CLOUDINARY_API_KEY", "key")
    monkeypatch.setenv("CLOUDINARY_API_SECRET", "secret")


def _context(db: Session):
    doctor = User(email="doctor-attachment@example.com", password_hash="hash", role=Role.MEDICO.value)
    patient_user = User(email="patient-attachment@example.com", password_hash="hash", role=Role.PACIENTE.value)
    db.add(doctor)
    db.add(patient_user)
    db.flush()
    patient = Patient(name="Paciente Anexo", cpf="12345678901", user_id=patient_user.id)
    db.add(patient)
    db.flush()
    entry = QueueEntry(
        patient_id=patient.id, symptoms="Teste", priority="VERDE", status="EM_ATENDIMENTO",
        doctor_user_id=doctor.id, entered_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.flush()
    record = ClinicalCareRecord(
        queue_entry_id=entry.id, patient_id=patient.id, doctor_user_id=doctor.id,
    )
    db.add(record)
    db.commit()
    for row in (doctor, patient_user, patient, record):
        db.refresh(row)
    return doctor, patient_user, patient, record


def test_upload_release_patient_download_and_remove_are_scoped(db: Session) -> None:
    doctor, patient_user, patient, record = _context(db)
    provider = FakeCloudinary()
    created = create_attachment(
        db, doctor_user_id=doctor.id, clinical_care_record_id=record.id,
        title="Hemograma", category="Laboratório", exam_date=None,
        filename="hemograma.pdf", content_type="application/pdf", content=b"%PDF",
        client=provider,
    )
    assert created.patient_id == patient.id
    assert list_patient_attachments(db, patient_user_id=patient_user.id) == ()

    set_patient_visibility(db, attachment_id=created.id, doctor_user_id=doctor.id, visible=True)
    assert [row.id for row in list_patient_attachments(db, patient_user_id=patient_user.id)] == [created.id]
    assert attachment_download_url(
        db, attachment_id=created.id, actor_user_id=patient_user.id,
        actor_is_patient=True, client=provider,
    ).startswith("https://api.cloudinary.com/")

    other_patient = User(email="other-patient@example.com", password_hash="hash", role=Role.PACIENTE.value)
    db.add(other_patient)
    db.commit()
    with pytest.raises(AttachmentAuthorizationError):
        attachment_download_url(
            db, attachment_id=created.id, actor_user_id=other_patient.id,
            actor_is_patient=True, client=provider,
        )

    remove_attachment(db, attachment_id=created.id, doctor_user_id=doctor.id, client=provider)
    assert provider.deleted
    assert list_patient_attachments(db, patient_user_id=patient_user.id) == ()


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [("script.exe", "application/octet-stream", b"bad"), ("empty.pdf", "application/pdf", b"")],
)
def test_upload_rejects_invalid_file_before_provider(db: Session, filename: str, content_type: str, content: bytes) -> None:
    doctor, _, _, record = _context(db)
    with pytest.raises(AttachmentError):
        create_attachment(
            db, doctor_user_id=doctor.id, clinical_care_record_id=record.id,
            title="Arquivo", category="Exame", exam_date=None, filename=filename,
            content_type=content_type, content=content, client=FakeCloudinary(),
        )

