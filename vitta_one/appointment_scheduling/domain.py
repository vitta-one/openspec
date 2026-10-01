"""Closed domain values for availability and consultation scheduling."""

from enum import Enum


class AvailabilitySlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BOOKED = "BOOKED"
    INACTIVE = "INACTIVE"

    @property
    def label(self) -> str:
        return {
            AvailabilitySlotStatus.AVAILABLE: "Disponível",
            AvailabilitySlotStatus.BOOKED: "Reservado",
            AvailabilitySlotStatus.INACTIVE: "Inativo",
        }[self]


class ConsultationStatus(str, Enum):
    AGENDADA = "AGENDADA"
    CONFIRMADA = "CONFIRMADA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"

    @property
    def label(self) -> str:
        return {
            ConsultationStatus.AGENDADA: "Agendada",
            ConsultationStatus.CONFIRMADA: "Confirmada",
            ConsultationStatus.EM_ANDAMENTO: "Em andamento",
            ConsultationStatus.CONCLUIDA: "Concluída",
            ConsultationStatus.CANCELADA: "Cancelada",
        }[self]
