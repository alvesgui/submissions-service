from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi import status as http_status

from src.adapters.inbound.http.dependencies import (
    get_create_use_case,
    get_get_use_case,
    get_list_use_case,
)
from src.adapters.inbound.http.schemas.submission import (
    CreateSubmissionRequest,
    CreateSubmissionResponse,
    ListSubmissionsResponse,
    SubmissionResponse,
)
from src.core.ports.inbound.use_cases import (
    CreateSubmissionInput,
    CreateSubmissionUseCase,
    GetSubmissionUseCase,
    ListSubmissionsInput,
    ListSubmissionsUseCase,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post(
    "",
    status_code=http_status.HTTP_201_CREATED,
    response_model=CreateSubmissionResponse,
    summary="Criar submissao",
    description="Recebe uma resposta discursiva, armazena no S3 e enfileira para correcao.",
)
async def create_submission(
    body: CreateSubmissionRequest,
    use_case: Annotated[CreateSubmissionUseCase, Depends(get_create_use_case)],
) -> CreateSubmissionResponse:
    output = await use_case.execute(
        CreateSubmissionInput(
            student_id=body.student_id,
            text=body.text,
        )
    )
    return CreateSubmissionResponse(
        id=output.id,
        student_id=output.student_id,
        s3_key=output.s3_key,
        status=output.status,
        created_at=output.created_at,
    )


@router.get(
    "/{submission_id}",
    status_code=http_status.HTTP_200_OK,
    response_model=SubmissionResponse,
    summary="Buscar submissao por ID",
    description="Retorna os detalhes de uma submissao incluindo status e nota quando disponivel.",
)
async def get_submission(
    submission_id: str,
    use_case: Annotated[GetSubmissionUseCase, Depends(get_get_use_case)],
) -> SubmissionResponse:
    output = await use_case.execute(submission_id)
    return SubmissionResponse(
        id=output.id,
        student_id=output.student_id,
        s3_key=output.s3_key,
        status=output.status,
        score=output.score,
        feedback=output.feedback,
        retry_count=output.retry_count,
        created_at=output.created_at,
        updated_at=output.updated_at,
    )


@router.get(
    "",
    status_code=http_status.HTTP_200_OK,
    response_model=ListSubmissionsResponse,
    summary="Listar submissoes por aluno",
    description="Lista todas as submissoes de um aluno com paginacao.",
)
async def list_submissions(
    use_case: Annotated[ListSubmissionsUseCase, Depends(get_list_use_case)],
    student_id: str = Query(..., description="ID do aluno", examples=["aluno-123"]),
    limit: int = Query(default=20, ge=1, le=100, description="Itens por pagina"),
    offset: int = Query(default=0, ge=0, description="Posicao inicial"),
) -> ListSubmissionsResponse:
    output = await use_case.execute(
        ListSubmissionsInput(
            student_id=student_id,
            limit=limit,
            offset=offset,
        )
    )
    return ListSubmissionsResponse(
        items=[
            SubmissionResponse(
                id=item.id,
                student_id=item.student_id,
                s3_key=item.s3_key,
                status=item.status,
                score=item.score,
                feedback=item.feedback,
                retry_count=item.retry_count,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in output.items
        ],
        total=output.total,
        limit=output.limit,
        offset=output.offset,
    )
