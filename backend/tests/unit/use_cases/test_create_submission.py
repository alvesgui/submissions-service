from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.use_cases.create_submission import CreateSubmissionUseCaseImpl
from src.core.ports.inbound.use_cases import CreateSubmissionInput
from src.core.ports.outbound.ports import QueuePublisher, StorageService, SubmissionRepository


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=SubmissionRepository)


@pytest.fixture
def queue() -> AsyncMock:
    return AsyncMock(spec=QueuePublisher)


@pytest.fixture
def storage() -> MagicMock:
    mock = MagicMock(spec=StorageService)
    mock.generate_key.return_value = "submissions/2026/03/test.txt"
    mock.upload_text = AsyncMock()
    return mock


@pytest.fixture
def use_case(
    repository: AsyncMock,
    queue: AsyncMock,
    storage: MagicMock,
) -> CreateSubmissionUseCaseImpl:
    return CreateSubmissionUseCaseImpl(
        repository=repository,
        queue=queue,
        storage=storage,
    )


@pytest.mark.unit
class TestCreateSubmission:
    async def test_retorna_output_com_status_pending(
        self, use_case: CreateSubmissionUseCaseImpl
    ) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Minha redacao.")
        output = await use_case.execute(input_data)
        assert output.status == "PENDING"

    async def test_retorna_output_com_student_id_correto(
        self, use_case: CreateSubmissionUseCaseImpl
    ) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Texto.")
        output = await use_case.execute(input_data)
        assert output.student_id == "aluno-1"

    async def test_chama_upload_do_storage(
        self, use_case: CreateSubmissionUseCaseImpl, storage: MagicMock
    ) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Texto da redacao.")
        await use_case.execute(input_data)
        storage.upload_text.assert_called_once()

    async def test_chama_save_do_repositorio(
        self, use_case: CreateSubmissionUseCaseImpl, repository: AsyncMock
    ) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Texto.")
        await use_case.execute(input_data)
        repository.save.assert_called_once()

    async def test_chama_publish_da_fila(
        self, use_case: CreateSubmissionUseCaseImpl, queue: AsyncMock
    ) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Texto.")
        await use_case.execute(input_data)
        queue.publish.assert_called_once()

    async def test_id_gerado_tem_26_caracteres(self, use_case: CreateSubmissionUseCaseImpl) -> None:
        input_data = CreateSubmissionInput(student_id="aluno-1", text="Texto.")
        output = await use_case.execute(input_data)
        assert len(output.id) == 26
