"""Database models used by Vitta-One."""

from .appointment import Consultation, ConsultationScheduleChange, ProfessionalAvailabilitySlot, ProfessionalWeeklySchedule
from .auth import AuthSession, User
from .clinic_settings import ClinicConfiguration, ClinicConfigurationChange
from .clinical_care import ClinicalCareRecord
from .clinical_documents import ClinicalAttachment, ClinicalAttachmentAudit
from .clinical_prescription import Prescription, PrescriptionItem
from .digital_signature import PrescriptionSignatureRequest, SignatureWebhookEvent
from .finance import (
    BillingCharge,
    BillingCustomer,
    BillingWebhookEvent,
    FinancialAudit,
    FinancialService,
    PatientAccount,
    PatientAccountItem,
    PaymentRecord,
)
from .patient_queue import Patient, PatientPortalInvitation, QueueEntry
from .professional import Professional, ProfessionalSpecialty, Specialty

__all__ = [
    "AuthSession", "BillingCharge", "BillingCustomer", "BillingWebhookEvent",
    "ClinicConfiguration", "ClinicConfigurationChange", "ClinicalAttachment",
    "ClinicalAttachmentAudit", "ClinicalCareRecord", "Consultation",
    "ConsultationScheduleChange", "FinancialAudit", "FinancialService", "Patient",
    "PatientAccount", "PatientAccountItem", "PatientPortalInvitation", "PaymentRecord",
    "Prescription", "PrescriptionItem", "PrescriptionSignatureRequest", "Professional",
    "ProfessionalAvailabilitySlot", "ProfessionalSpecialty", "ProfessionalWeeklySchedule",
    "QueueEntry", "SignatureWebhookEvent", "Specialty", "User",
]

