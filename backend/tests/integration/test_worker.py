import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.integration.conftest import make_test_settings

from src.adapters.outbound.postgres.repositories.submission_repo import PostgresSubmissionRepository
from src.adapters.outbound.s3.storage import S3StorageService
from src.application.use_cases.process_submission import ProcessSubmissionUseCaseImpl

TEXTO_BOM = (
    "A inteligencia artificial representa uma revolucao tecnologica sem precedentes. "
    "Por isso, devemos analisar seus impactos com cuidado e responsabilidade. "
    "Alem disso, e fundamental considerar as implicacoes eticas envolvidas. "
    "No entanto, nao podemos ignorar os beneficios que essa tecnologia oferece. "
    "Em suma, o equilibrio entre inovacao e regulacao e essencial para o progresso. "
    "Dessa forma, construiremos uma sociedade mais justa e sustentavel para todos.\n"
    "Portanto, o debate sobre inteligencia artificial deve ser amplo e inclusivo."
)

TEXTO_CURTO = "Texto muito curto para testes."


@pytest.mark.integration
class TestProcessamentoCompleto:
    """
    Testa o fluxo completo:
    POST /submissions → ProcessSubmissionUseCase → GET /submissions/{id}
    """

    async def test_submissao_processada_muda_para_completed(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        # Cria a submissao via API
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-worker", "text": TEXTO_BOM},
        )
        assert create.status_code == 201
        submission_id = create.json()["id"]

        # Processa via use case (simula o worker)
        settings = make_test_settings()
        repository = PostgresSubmissionRepository(session=db_session)
        storage = S3StorageService(settings=settings)
        use_case = ProcessSubmissionUseCaseImpl(
            repository=repository,
            storage=storage,
        )
        await use_case.execute(submission_id)
        await db_session.commit()

        # Verifica o resultado via API
        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        body = response.json()

        assert body["status"] == "COMPLETED"
        assert body["score"] is not None
        assert body["feedback"] is not None
        assert float(body["score"]) >= 0.0

    async def test_texto_rico_recebe_nota_alta(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-rico", "text": TEXTO_BOM},
        )
        submission_id = create.json()["id"]

        settings = make_test_settings()
        repository = PostgresSubmissionRepository(session=db_session)
        storage = S3StorageService(settings=settings)
        use_case = ProcessSubmissionUseCaseImpl(
            repository=repository,
            storage=storage,
        )
        await use_case.execute(submission_id)
        await db_session.commit()

        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        body = response.json()

        assert float(body["score"]) >= 6.0
        assert "APROVADO" in body["feedback"]

    async def test_texto_curto_recebe_nota_baixa(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-curto", "text": TEXTO_CURTO + " " * 10},
        )
        submission_id = create.json()["id"]

        settings = make_test_settings()
        repository = PostgresSubmissionRepository(session=db_session)
        storage = S3StorageService(settings=settings)
        use_case = ProcessSubmissionUseCaseImpl(
            repository=repository,
            storage=storage,
        )
        await use_case.execute(submission_id)
        await db_session.commit()

        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        body = response.json()

        assert float(body["score"]) < 6.0

    async def test_submissao_processada_tem_feedback_com_criterios(
        self,
        test_client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-feedback", "text": TEXTO_BOM},
        )
        submission_id = create.json()["id"]

        settings = make_test_settings()
        repository = PostgresSubmissionRepository(session=db_session)
        storage = S3StorageService(settings=settings)
        use_case = ProcessSubmissionUseCaseImpl(
            repository=repository,
            storage=storage,
        )
        await use_case.execute(submission_id)
        await db_session.commit()

        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        feedback = response.json()["feedback"]

        # Verifica que o feedback contem todos os criterios
        assert "Extensao do texto" in feedback
        assert "Riqueza de vocabulario" in feedback
        assert "Estrutura e pontuacao" in feedback
        assert "Coesao textual" in feedback
        assert "Nota final" in feedback

    async def test_submissao_pending_tem_score_nulo(
        self,
        test_client: AsyncClient,
    ) -> None:
        """Score deve ser null antes de processar."""
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-pending", "text": TEXTO_BOM},
        )
        submission_id = create.json()["id"]

        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        body = response.json()

        assert body["status"] == "PENDING"
        assert body["score"] is None
        assert body["feedback"] is None
