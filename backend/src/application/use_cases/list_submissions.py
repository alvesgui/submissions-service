from src.core.ports.inbound.use_cases import (
    ListSubmissionsInput,
    ListSubmissionsOutput,
    ListSubmissionsUseCase,
    SubmissionOutput,
)
from src.core.ports.outbound.ports import SubmissionRepository


class ListSubmissionsUseCaseImpl(ListSubmissionsUseCase):
    """
    Lista submissoes de um aluno com paginacao simples.
    """

    def __init__(self, repository: SubmissionRepository) -> None:
        self._repository = repository

    async def execute(self, input_data: ListSubmissionsInput) -> ListSubmissionsOutput:
        # Busca os itens e o total
        submissions = await self._repository.find_by_student_id(
            student_id=input_data.student_id,
            limit=input_data.limit,
            offset=input_data.offset,
        )

        total = await self._repository.count_by_student_id(
            student_id=input_data.student_id,
        )

        items = [
            SubmissionOutput(
                id=sub.id,
                student_id=sub.student_id,
                s3_key=sub.s3_key,
                status=sub.status.value,
                score=sub.score_value,
                feedback=sub.feedback,
                retry_count=sub.retry_count,
                created_at=sub.created_at.isoformat(),
                updated_at=sub.updated_at.isoformat(),
            )
            for sub in submissions
        ]

        return ListSubmissionsOutput(
            items=items,
            total=total,
            limit=input_data.limit,
            offset=input_data.offset,
        )
