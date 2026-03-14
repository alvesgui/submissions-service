import pytest
from httpx import AsyncClient

VALID_TEXT = (
    "A tecnologia transformou a sociedade moderna de diversas formas. "
    "Por isso, devemos refletir sobre seus impactos. "
    "Alem disso, e necessario considerar os aspectos sociais envolvidos. "
    "No entanto, nao podemos ignorar os beneficios que ela oferece. "
    "Em suma, o equilibrio entre inovacao e responsabilidade e essencial."
)


@pytest.mark.integration
class TestCreateSubmission:
    async def test_cria_submissao_retorna_201(self, test_client: AsyncClient) -> None:
        response = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1", "text": VALID_TEXT},
        )
        assert response.status_code == 201

    async def test_cria_submissao_retorna_campos_corretos(self, test_client: AsyncClient) -> None:
        response = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1", "text": VALID_TEXT},
        )
        body = response.json()
        assert body["student_id"] == "aluno-1"
        assert body["status"] == "PENDING"
        assert len(body["id"]) == 26
        assert "s3_key" in body
        assert "created_at" in body

    async def test_cria_submissao_texto_curto_retorna_422(self, test_client: AsyncClient) -> None:
        response = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1", "text": "curto"},
        )
        assert response.status_code == 422

    async def test_cria_submissao_sem_student_id_retorna_422(
        self, test_client: AsyncClient
    ) -> None:
        response = await test_client.post(
            "/api/v1/submissions",
            json={"text": VALID_TEXT},
        )
        assert response.status_code == 422

    async def test_cria_submissao_sem_text_retorna_422(self, test_client: AsyncClient) -> None:
        response = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1"},
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestGetSubmission:
    async def test_busca_submissao_existente_retorna_200(self, test_client: AsyncClient) -> None:
        # Cria
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1", "text": VALID_TEXT},
        )
        submission_id = create.json()["id"]

        # Busca
        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        assert response.status_code == 200

    async def test_busca_submissao_retorna_campos_completos(self, test_client: AsyncClient) -> None:
        create = await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-1", "text": VALID_TEXT},
        )
        submission_id = create.json()["id"]

        response = await test_client.get(f"/api/v1/submissions/{submission_id}")
        body = response.json()

        assert body["id"] == submission_id
        assert body["status"] == "PENDING"
        assert body["score"] is None
        assert body["feedback"] is None
        assert body["retry_count"] == 0
        assert "created_at" in body
        assert "updated_at" in body

    async def test_busca_submissao_inexistente_retorna_404(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/api/v1/submissions/ID-INEXISTENTE")
        assert response.status_code == 404

    async def test_erro_404_tem_formato_correto(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/api/v1/submissions/ID-INEXISTENTE")
        body = response.json()
        assert body["error"] == "NOT_FOUND"
        assert "status_code" in body
        assert "message" in body


@pytest.mark.integration
class TestListSubmissions:
    async def test_lista_submissoes_retorna_200(self, test_client: AsyncClient) -> None:
        response = await test_client.get(
            "/api/v1/submissions", params={"student_id": "aluno-sem-dados"}
        )
        assert response.status_code == 200

    async def test_lista_retorna_zero_quando_aluno_nao_tem_submissoes(
        self, test_client: AsyncClient
    ) -> None:
        response = await test_client.get("/api/v1/submissions", params={"student_id": "aluno-novo"})
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []

    async def test_lista_retorna_submissoes_do_aluno(self, test_client: AsyncClient) -> None:
        # Cria 2 submissoes
        for _ in range(2):
            await test_client.post(
                "/api/v1/submissions",
                json={"student_id": "aluno-lista", "text": VALID_TEXT},
            )

        response = await test_client.get(
            "/api/v1/submissions", params={"student_id": "aluno-lista"}
        )
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    async def test_lista_nao_mistura_alunos(self, test_client: AsyncClient) -> None:
        await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-a", "text": VALID_TEXT},
        )
        await test_client.post(
            "/api/v1/submissions",
            json={"student_id": "aluno-b", "text": VALID_TEXT},
        )

        response = await test_client.get("/api/v1/submissions", params={"student_id": "aluno-a"})
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["student_id"] == "aluno-a"

    async def test_paginacao_limit_e_offset(self, test_client: AsyncClient) -> None:
        for _ in range(3):
            await test_client.post(
                "/api/v1/submissions",
                json={"student_id": "aluno-pag", "text": VALID_TEXT},
            )

        response = await test_client.get(
            "/api/v1/submissions",
            params={"student_id": "aluno-pag", "limit": 2, "offset": 0},
        )
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["limit"] == 2
        assert body["offset"] == 0

    async def test_sem_student_id_retorna_422(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/api/v1/submissions")
        assert response.status_code == 422


@pytest.mark.integration
class TestHealthCheck:
    async def test_health_retorna_200(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
