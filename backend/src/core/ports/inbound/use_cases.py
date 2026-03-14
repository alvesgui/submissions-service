from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class CreateSubmissionInput:
    """Dados que chegam do HTTP para criar uma submissao."""

    student_id: str
    text: str


@dataclass(frozen=True)
class CreateSubmissionOutput:
    """Dados retornados ao HTTP apos criar uma submissao."""

    id: str
    student_id: str
    s3_key: str
    status: str
    created_at: str


@dataclass(frozen=True)
class SubmissionOutput:
    """
    Dados completos de uma submissao.
    Usado no GET /submissions/{id} e na listagem.
    """

    id: str
    student_id: str
    s3_key: str
    status: str
    score: Decimal | None
    feedback: str | None
    retry_count: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ListSubmissionsInput:
    """Parametros para listar submissoes de um aluno."""

    student_id: str
    limit: int = 20
    offset: int = 0


@dataclass(frozen=True)
class ListSubmissionsOutput:
    """Resultado paginado da listagem."""

    items: list[SubmissionOutput]
    total: int
    limit: int
    offset: int

# Interfaces dos Use Cases (portas de entrada)

class CreateSubmissionUseCase(ABC):
    """
    Orquestra a criacao de uma submissao:
    1. Gera a chave S3 e faz upload do texto
    2. Salva o job no banco com status PENDING
    3. Publica mensagem na fila SQS
    """

    @abstractmethod
    async def execute(self, input_data: CreateSubmissionInput) -> CreateSubmissionOutput:
        raise NotImplementedError


class GetSubmissionUseCase(ABC):
    """
    Busca uma submissao pelo ID.
    Dispara SubmissionNotFoundError se nao existir.
    """

    @abstractmethod
    async def execute(self, submission_id: str) -> SubmissionOutput:
        raise NotImplementedError


class ListSubmissionsUseCase(ABC):
    """Lista submissoes de um aluno com paginacao."""

    @abstractmethod
    async def execute(self, input_data: ListSubmissionsInput) -> ListSubmissionsOutput:
        raise NotImplementedError


class ProcessSubmissionUseCase(ABC):
    """
    Logica de correcao (worker)
    1. Busca a submissao no banco
    2. Le o texto do S3
    3. Calcula a nota
    4. Atualiza status e nota no banco
    """

    @abstractmethod
    async def execute(self, submission_id: str) -> None:
        raise NotImplementedError
