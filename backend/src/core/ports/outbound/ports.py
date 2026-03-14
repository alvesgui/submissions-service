from abc import ABC, abstractmethod

from src.core.domain.submission import Submission


class SubmissionRepository(ABC):
    """
    Porta de saida - contrato de persistencia.
    """

    @abstractmethod
    async def save(self, submission: Submission) -> None:
        """Persiste uma nova submissao no banco."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, submission: Submission) -> None:
        """Atualiza uma submissao existente (status, score, feedback)."""
        raise NotImplementedError

    @abstractmethod
    async def find_by_id(self, submission_id: str) -> Submission | None:
        """
        Busca por ID.
        """
        raise NotImplementedError

    @abstractmethod
    async def find_by_student_id(
        self,
        student_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Submission]:
        """
        Lista submissoes de um aluno com paginacao.
        """
        raise NotImplementedError

    @abstractmethod
    async def count_by_student_id(self, student_id: str) -> int:
        """Conta total de submissoes de um aluno."""
        raise NotImplementedError


class QueuePublisher(ABC):
    """
    Porta de saida, contrato de publicacao em fila.

    Em desenvolvimento: SQS via LocalStack.
    Em producao: SQS real da AWS.
    """

    @abstractmethod
    async def publish(self, submission_id: str) -> None:
        """
        Publica uma mensagem na fila para processamento assincrono.
        """
        raise NotImplementedError


class StorageService(ABC):
    """
    Porta de saida, contrato de armazenamento de objetos.

    Em desenvolvimento: LocalStack S3.
    Em producao: AWS S3 real. boto3, so muda endpoint e credenciais.
    """

    @abstractmethod
    async def upload_text(self, key: str, content: str) -> str:
        """
        Faz upload do texto da submissao.

        Args:
            key: Caminho do objeto (ex: "submissions/2026/03/ULID.txt")
            content: Texto da resposta discursiva do aluno

        Returns:
            A chave do objeto salvo (confirmacao)
        """
        raise NotImplementedError

    @abstractmethod
    async def download_text(self, key: str) -> str:
        """
        Baixa o texto de uma submissao.
        Usado pelo worker para ler o texto antes de corrigir.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_key(self, submission_id: str) -> str:
        """
        Gera o caminho do objeto no storage.
        Exemplo de retorno: "submissions/2026/03/01ARZ3NDEKTSV4RRFFQ69G5FAV.txt"
        """
        raise NotImplementedError
