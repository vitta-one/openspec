"""Closed set of roles supported by Vitta-One."""

from enum import Enum


class Role(str, Enum):
    """Roles defined by the project domain."""

    ADMINISTRADOR = "ADMINISTRADOR"
    RECEPCIONISTA = "RECEPCIONISTA"
    MEDICO = "MEDICO"
    FINANCEIRO = "FINANCEIRO"
    PACIENTE = "PACIENTE"

    @property
    def label(self) -> str:
        """Human-readable role label in Portuguese."""
        return {
            Role.ADMINISTRADOR: "Administrador",
            Role.RECEPCIONISTA: "Recepcionista",
            Role.MEDICO: "Médico",
            Role.FINANCEIRO: "Financeiro",
            Role.PACIENTE: "Paciente",
        }[self]

    @property
    def dashboard_path(self) -> str:
        """Protected landing route associated with the role."""
        return {
            Role.ADMINISTRADOR: "/admin",
            Role.RECEPCIONISTA: "/recepcao",
            Role.MEDICO: "/medico",
            Role.FINANCEIRO: "/financeiro",
            Role.PACIENTE: "/paciente",
        }[self]
