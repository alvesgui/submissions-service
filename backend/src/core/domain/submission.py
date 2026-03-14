from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from ulid import ULID

from src.core.domain.score import Score
from src.core.domain.submission_status import SubmissionStatus


@dataclass
class Submission:
    """
    Entidade principal do dominio.

    Sumission representa uma resposta discursiva enviada por um aluno
    e o ciclo de vida da sua correcao completo.
    """

    id: str
    student_id: str
    s3_key: str

    status: SubmissionStatus = field(default=SubmissionStatus.PENDING)
    score: Score | None = field(default=None)
    feedback: str | None = field(default=None)
    retry_count: int = field(default=0)

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(cls, student_id: str, s3_key: str) -> "Submission":
        """
        Cria uma nova submissao.
        """
        now = datetime.now(UTC)
        return cls(
            id=str(ULID()),
            student_id=student_id,
            s3_key=s3_key,
            status=SubmissionStatus.PENDING,
            score=None,
            feedback=None,
            retry_count=0,
            created_at=now,
            updated_at=now,
        )

    # Mudancas de estado de correcao

    def start_processing(self) -> None:
        """
        Marca a submissao como em processamento.
        Chamado pelo worker quando consome a mensagem da fila SQS.
        """
        self._transition_to(SubmissionStatus.PROCESSING)

    def complete(self, score: Score, feedback: str) -> None:
        """
        Finaliza a correcao com sucesso.
        So pode ser chamado se o status atual for PROCESSING.
        """
        self._transition_to(SubmissionStatus.COMPLETED)
        self.score = score
        self.feedback = feedback
        self.updated_at = datetime.now(UTC)

    def fail(self) -> None:
        """
        Marca a correcao como falha definitiva.
        Chamado quando retry_count atinge o limite(3).
        """
        self.retry_count += 1
        self._transition_to(SubmissionStatus.FAILED)

    def increment_retry(self) -> None:
        """
        Incrementa tentativa sem marcar como FAILED ainda.
        Usado quando o worker vai tentar novamente antes do limite.
        """
        self.retry_count += 1
        self.updated_at = datetime.now(UTC)

    @property
    def is_corrected(self) -> bool:
        """True se a correcao foi concluida com nota."""
        return self.status == SubmissionStatus.COMPLETED and self.score is not None

    @property
    def score_value(self) -> Decimal | None:
        """Retorna o valor decimal da nota, ou None se nao corrigida."""
        return self.score.value if self.score else None

    # Validacoes de movimentacoes de status

    def _transition_to(self, next_status: SubmissionStatus) -> None:
        """
        Valida e executa a transicao de status, verifica se a transicao nao for permitida.
        """
        if not self.status.can_transition_to(next_status):
            raise InvalidStatusTransitionError(
                current=self.status,
                next_status=next_status,
            )
        self.status = next_status
        self.updated_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return (
            f"Submission(id={self.id!r}, "
            f"student_id={self.student_id!r}, "
            f"status={self.status.value!r})"
        )


class DomainError(Exception):
    """Base para todos os erros de dominio."""


class InvalidStatusTransitionError(DomainError):
    """Levantada quando se tenta fazer uma transicao de status invalida/nao permitida."""

    def __init__(
        self,
        current: SubmissionStatus,
        next_status: SubmissionStatus,
    ) -> None:
        self.current = current
        self.next_status = next_status
        super().__init__(
            f"Nao e possivel transicionar de {current.value!r} para {next_status.value!r}"
        )


class SubmissionNotFoundError(DomainError):
    """Erro quando uma submissao nao e encontrada no repositorio."""

    def __init__(self, submission_id: str) -> None:
        self.submission_id = submission_id
        super().__init__(f"Submissao {submission_id!r} nao encontrada")
