from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.process_submission import ProcessSubmissionUseCaseImpl
from src.core.domain.submission import Submission, SubmissionNotFoundError
from src.core.domain.submission_status import SubmissionStatus
from src.core.ports.outbound.ports import StorageService, SubmissionRepository


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock(spec=SubmissionRepository)


@pytest.fixture
def storage() -> AsyncMock:
    return AsyncMock(spec=StorageService)


@pytest.fixture
def use_case(repository: AsyncMock, storage: AsyncMock) -> ProcessSubmissionUseCaseImpl:
    return ProcessSubmissionUseCaseImpl(repository=repository, storage=storage)


@pytest.fixture
def submission() -> Submission:
    return Submission.create(student_id="aluno-1", s3_key="submissions/test.txt")


@pytest.mark.unit
class TestProcessSubmission:
    async def test_marca_como_completed_apos_processar(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
        repository: AsyncMock,
        storage: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        storage.download_text.return_value = (
            "A tecnologia transformou a sociedade moderna de diversas formas. "
            "Por isso, devemos refletir sobre seus impactos. "
            "Alem disso, e necessario considerar os aspectos sociais. "
            "No entanto, existem desafios a serem superados. "
            "Em suma, o progresso tecnologico exige responsabilidade coletiva. "
            "Dessa forma, podemos construir um futuro mais equilibrado e justo "
            "para todas as pessoas que vivem em nossa sociedade globalizada."
        )

        await use_case.execute(submission.id)

        assert submission.status == SubmissionStatus.COMPLETED
        assert submission.score is not None

    async def test_levanta_not_found_quando_nao_existe(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
        repository: AsyncMock,
    ) -> None:
        repository.find_by_id.return_value = None
        with pytest.raises(SubmissionNotFoundError):
            await use_case.execute("id-inexistente")

    async def test_incrementa_retry_em_caso_de_falha(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
        repository: AsyncMock,
        storage: AsyncMock,
        submission: Submission,
    ) -> None:
        repository.find_by_id.return_value = submission
        storage.download_text.side_effect = Exception("S3 indisponivel")

        with pytest.raises(Exception):
            await use_case.execute(submission.id)

        assert submission.retry_count == 1

    async def test_marca_como_failed_apos_max_retries(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
        repository: AsyncMock,
        storage: AsyncMock,
    ) -> None:
        # Submissao com retry_count ja no limite
        submission = Submission.create(student_id="a", s3_key="k")
        submission.retry_count = ProcessSubmissionUseCaseImpl.MAX_RETRIES - 1
        repository.find_by_id.return_value = submission
        storage.download_text.side_effect = Exception("Falha persistente")

        with pytest.raises(Exception):
            await use_case.execute(submission.id)

        assert submission.status == SubmissionStatus.FAILED

    async def test_avalia_texto_curto_com_nota_baixa(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
    ) -> None:
        score, _ = use_case._evaluate("Texto curto.")
        assert float(score) < 5.0

    async def test_avalia_texto_rico_com_nota_alta(
        self,
        use_case: ProcessSubmissionUseCaseImpl,
    ) -> None:
        texto_rico = (
            "A inteligencia artificial representa uma revolucao tecnologica sem precedentes. "
            "Por isso, devemos analisar seus impactos com cuidado e responsabilidade. "
            "Alem disso, e fundamental considerar as implicacoes eticas envolvidas. "
            "No entanto, nao podemos ignorar os beneficios que essa tecnologia oferece. "
            "Em suma, o equilibrio entre inovacao e regulacao e essencial para o progresso. "
            "Dessa forma, construiremos uma sociedade mais justa, igualitaria e sustentavel.\n"
            "Portanto, o debate sobre inteligencia artificial deve ser amplo e inclusivo."
        )
        score, feedback = use_case._evaluate(texto_rico)
        assert float(score) >= 7.0
        assert "APROVADO" in feedback
