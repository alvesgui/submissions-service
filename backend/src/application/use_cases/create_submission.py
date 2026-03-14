from src.core.domain.submission import Submission
from src.core.ports.inbound.use_cases import (
    CreateSubmissionInput,
    CreateSubmissionOutput,
    CreateSubmissionUseCase,
)
from src.core.ports.outbound.ports import (
    QueuePublisher,
    StorageService,
    SubmissionRepository,
)


class CreateSubmissionUseCaseImpl(CreateSubmissionUseCase):
    """
    Implementacao do caso de uso de criacao de submissao.

    Recebe as dependencias pelo construtor (injecao de dependencia).
    """

    def __init__(
        self,
        repository: SubmissionRepository,
        queue: QueuePublisher,
        storage: StorageService,
    ) -> None:
        self._repository = repository
        self._queue = queue
        self._storage = storage

    async def execute(self, input_data: CreateSubmissionInput) -> CreateSubmissionOutput:
        # 1: gera a chave e faz upload do texto para o S3
        # O texto do aluno fica no S3 - o banco so guarda a referencia (chave)
        s3_key = self._storage.generate_key(submission_id="temp")
        await self._storage.upload_text(key=s3_key, content=input_data.text)

        # 2: cria a entidade e persiste no banco com status `PENDING`
        submission = Submission.create(
            student_id=input_data.student_id,
            s3_key=s3_key,
        )
        await self._repository.save(submission)

        # 3: publica o ID na fila para o worker processar de forma assincrona, como dito antes busca o mais recente.
        await self._queue.publish(submission_id=submission.id)

        return CreateSubmissionOutput(
            id=submission.id,
            student_id=submission.student_id,
            s3_key=submission.s3_key,
            status=submission.status.value,
            created_at=submission.created_at.isoformat(),
        )
