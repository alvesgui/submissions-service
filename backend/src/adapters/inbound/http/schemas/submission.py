from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

# Request Schemas

class CreateSubmissionRequest(BaseModel):
    """
    Body do POST /submissions.

    Pydantic valida automaticamente:
    - student_id nao pode ser vazio
    - text precisa ter pelo menos 10 caracteres
    Se falhar, retorna 422 automaticamente com detalhes do erro.
    """

    student_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Identificador unico do aluno",
        examples=["aluno-123"],
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Texto da resposta discursiva",
        examples=["A tecnologia transformou a sociedade moderna..."],
    )

    @field_validator("student_id")
    @classmethod
    def student_id_nao_pode_ter_espacos(cls, v: str) -> str:
        if v != v.strip():
            raise ValueError("student_id nao pode ter espacos no inicio ou fim")
        return v


#Response Schemas


class CreateSubmissionResponse(BaseModel):
    """Resposta do POST /submissions — retorna 201."""

    id: str
    student_id: str
    s3_key: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    """
    Resposta do GET /submissions/{id}.
    score e feedback sao None enquanto PENDING ou PROCESSING.
    """

    id: str
    student_id: str
    s3_key: str
    status: str
    score: Decimal | None = None
    feedback: str | None = None
    retry_count: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ListSubmissionsResponse(BaseModel):
    """
    Resposta do GET /submissions?student_id=xxx.
    Inclui metadados de paginacao para o frontend.
    """

    items: list[SubmissionResponse]
    total: int = Field(description="Total de submissoes do aluno")
    limit: int = Field(description="Limite de itens por pagina")
    offset: int = Field(description="Posicao inicial da pagina atual")

    model_config = {"from_attributes": True}


# Error Schema


class ErrorResponse(BaseModel):
    """
    Formato padrao de erro. Todos os erros da API retornam esse formato.

    Exemplo:
    {
        "error": "NOT_FOUND",
        "message": "Submissao '1111...' nao encontrada",
        "status_code": 404
    }
    """

    error: str
    message: str
    status_code: int
