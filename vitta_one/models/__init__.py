"""Database models used by Vitta-One."""

from .appointment import Consultation, ProfessionalAvailabilitySlot
from .auth import AuthSession, User
from .clinical_care import ClinicalCareRecord
from .clinical_prescription import Prescription, PrescriptionItem
from .patient_queue import Patient, QueueEntry
from .professional import Professional, ProfessionalSpecialty, Specialty

__all__ = ["AuthSession", "ClinicalCareRecord", "Consultation", "Patient", "Prescription", "PrescriptionItem", "Professional", "ProfessionalAvailabilitySlot", "ProfessionalSpecialty", "QueueEntry", "Specialty", "User"]
