"""Database models used by Vitta-One."""

from .appointment import Consultation, ProfessionalAvailabilitySlot
from .auth import AuthSession, User
from .patient_queue import Patient, QueueEntry
from .professional import Professional, ProfessionalSpecialty, Specialty

__all__ = ["AuthSession", "Consultation", "Patient", "Professional", "ProfessionalAvailabilitySlot", "ProfessionalSpecialty", "QueueEntry", "Specialty", "User"]
