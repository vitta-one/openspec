"""Closed domain values for the patient reception queue."""

from enum import Enum


class QueuePriority(str, Enum):
    """Operational priority informed outside Vitta-One."""

    VERMELHO = "VERMELHO"
    AMARELO = "AMARELO"
    VERDE = "VERDE"

    @property
    def rank(self) -> int:
        return {
            QueuePriority.VERMELHO: 0,
            QueuePriority.AMARELO: 1,
            QueuePriority.VERDE: 2,
        }[self]

    @property
    def label(self) -> str:
        return {
            QueuePriority.VERMELHO: "Vermelho",
            QueuePriority.AMARELO: "Amarelo",
            QueuePriority.VERDE: "Verde",
        }[self]


class QueueStatus(str, Enum):
    """Lifecycle for one passage through the reception queue."""

    AGUARDANDO = "AGUARDANDO"
    EM_ATENDIMENTO = "EM_ATENDIMENTO"
    FINALIZADO = "FINALIZADO"
    RETIRADO = "RETIRADO"
