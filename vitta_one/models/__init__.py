"""Database models used by Vitta-One."""

from .auth import AuthSession, User
from .patient_queue import Patient, QueueEntry

__all__ = ["AuthSession", "Patient", "QueueEntry", "User"]
