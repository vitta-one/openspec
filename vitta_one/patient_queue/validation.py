"""Shared validation for operational queue inputs."""

from vitta_one.patient_queue.domain import QueuePriority


class QueuePayloadValidationError(ValueError):
    """Raised when symptoms or priority do not satisfy the queue contract."""


def normalize_queue_symptoms(value: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise QueuePayloadValidationError("Informe os sintomas relatados.")
    if len(clean) > 4000:
        raise QueuePayloadValidationError("O relato de sintomas excede o limite permitido.")
    return clean


def parse_queue_priority(value: str | QueuePriority) -> QueuePriority:
    try:
        return value if isinstance(value, QueuePriority) else QueuePriority(str(value))
    except ValueError as exc:
        raise QueuePayloadValidationError("Selecione uma prioridade válida.") from exc
