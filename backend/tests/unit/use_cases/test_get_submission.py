from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.get_submission import GetSubmissionUseCaseImpl
from src.core.domain.submission import Submission, SubmissionNotFoundError
from src.core.ports.outbound.ports import SubmissionRepository


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=SubmissionRepository)


@pytest.fixture
def use_case(repository: AsyncMock) -> GetSubmissionUseCaseImpl:
    return GetSubmissionUseCaseImpl(repository=repository)


@pytest.fixture
def submission() -> Submission:
    return Submission.create(student_id="aluno-1", s3_key="submissions/test.txt")


@pytest.mark.unit
class TestGetSubmission:
    async def test_retorna_output_quando_encontra(
        self,
        use_case: GetSubmissionUseCaseImpl,
        repository: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        output = await use_case.execute(submission.id)
        assert output.id == submission.id
        assert output.student_id == "aluno-1"

    async def test_retorna_status_correto(
        self,
        use_case: GetSubmissionUseCaseImpl,
        repository: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        output = await use_case.execute(submission.id)
        assert output.status == "PENDING"

    async def test_levanta_not_found_quando_nao_existe(
        self,
        use_case: GetSubmissionUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        repository.find_by_id.return_value = None
        with pytest.raises(SubmissionNotFoundError):
            await use_case.execute("id-inexistente")

    async def test_score_none_quando_pending(
        self,
        use_case: GetSubmissionUseCaseImpl,
        repository: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        output = await use_case.execute(submission.id)
        assert output.score is None

    async def test_chama_repositorio_com_id_correto(
        self,
        use_case: GetSubmissionUseCaseImpl,
        repository: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        await use_case.execute(submission.id)
        repository.find_by_id.assert_called_once_with(submission.id)
