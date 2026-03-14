from enum import Enum


class SubmissionStatus(str, Enum):
    """
    Value Object que representa o ciclo de vida de uma submissão.
    Fluxo válido:
        PENDING -> PROCESSING -> COMPLETED
                              -> FAILED
    """

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    def can_transition_to(self, next_status: "SubmissionStatus") -> bool:
        """
        Valida se a transicao de estado e permitida.
        """
        allowed: dict[SubmissionStatus, set[SubmissionStatus]] = {
            SubmissionStatus.PENDING: {SubmissionStatus.PROCESSING},
            SubmissionStatus.PROCESSING: {
                SubmissionStatus.COMPLETED,
                SubmissionStatus.FAILED,
            },
            SubmissionStatus.COMPLETED: set(),
            SubmissionStatus.FAILED: set(),
        }
        return next_status in allowed[self]

    @property
    def is_terminal(self) -> bool:
        """Retorna True se o status nao pode mais mudar."""
        return self in {SubmissionStatus.COMPLETED, SubmissionStatus.FAILED}

    @property
    def is_processable(self) -> bool:
        """
        Retorna True se pode ser processada pelo worker.
        """
        return self == SubmissionStatus.PENDING
