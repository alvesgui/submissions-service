from src.core.domain.submission import SubmissionNotFoundError
from src.core.ports.inbound.use_cases import (
    GetSubmissionUseCase,
    SubmissionOutput,
)
from src.core.ports.outbound.ports import SubmissionRepository


class GetSubmissionUseCaseImpl(GetSubmissionUseCase):
    """
    Busca uma submissao pelo ID e retorna seus detalhes completos.
    """

    def __init__(self, repository: SubmissionRepository) -> None:
        self._repository = repository

    async def execute(self, submission_id: str) -> SubmissionOutput:
        submission = await self._repository.find_by_id(submission_id)

        if submission is None:
            raise SubmissionNotFoundError(submission_id)

        return SubmissionOutput(
            id=submission.id,
            student_id=submission.student_id,
            s3_key=submission.s3_key,
            status=submission.status.value,
            score=submission.score_value,
            feedback=submission.feedback,
            retry_count=submission.retry_count,
            created_at=submission.created_at.isoformat(),
            updated_at=submission.updated_at.isoformat(),
        )
