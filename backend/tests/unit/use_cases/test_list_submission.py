from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.list_submissions import ListSubmissionsUseCaseImpl
from src.core.domain.submission import Submission
from src.core.ports.inbound.use_cases import ListSubmissionsInput
from src.core.ports.outbound.ports import SubmissionRepository


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=SubmissionRepository)


@pytest.fixture
def use_case(repository: AsyncMock) -> ListSubmissionsUseCaseImpl:
    return ListSubmissionsUseCaseImpl(repository=repository)


@pytest.mark.unit
class TestListSubmissions:
    async def test_retorna_lista_de_itens(
        self,
        use_case: ListSubmissionsUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        submissions = [
            Submission.create(student_id="aluno-1", s3_key="k1"),
            Submission.create(student_id="aluno-1", s3_key="k2"),
        ]
        repository.find_by_student_id.return_value = submissions
        repository.count_by_student_id.return_value = 2

        input_data = ListSubmissionsInput(student_id="aluno-1")
        output = await use_case.execute(input_data)

        assert len(output.items) == 2
        assert output.total == 2

    async def test_retorna_lista_vazia_quando_nao_ha_submissoes(
        self,
        use_case: ListSubmissionsUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        repository.find_by_student_id.return_value = []
        repository.count_by_student_id.return_value = 0

        input_data = ListSubmissionsInput(student_id="aluno-sem-submissoes")
        output = await use_case.execute(input_data)

        assert output.items == []
        assert output.total == 0

    async def test_repassa_limit_e_offset_corretos(
        self,
        use_case: ListSubmissionsUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        repository.find_by_student_id.return_value = []
        repository.count_by_student_id.return_value = 0

        input_data = ListSubmissionsInput(student_id="aluno-1", limit=5, offset=10)
        output = await use_case.execute(input_data)

        repository.find_by_student_id.assert_called_once_with(
            student_id="aluno-1", limit=5, offset=10
        )
        assert output.limit == 5
        assert output.offset == 10

    async def test_total_reflete_count_do_repositorio(
        self,
        use_case: ListSubmissionsUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        repository.find_by_student_id.return_value = []
        repository.count_by_student_id.return_value = 47

        input_data = ListSubmissionsInput(student_id="aluno-1")
        output = await use_case.execute(input_data)

        assert output.total == 47
