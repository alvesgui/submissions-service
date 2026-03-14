from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.domain.submission import (
    DomainError,
    InvalidStatusTransitionError,
    SubmissionNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registra todos os handlers de excecao na aplicacao.
    """

    @app.exception_handler(SubmissionNotFoundError)
    async def submission_not_found_handler(
        _request: Request,
        exc: SubmissionNotFoundError,
    ) -> JSONResponse:
        """Submissao nao encontrada -> 404."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "NOT_FOUND",
                "message": str(exc),
                "status_code": 404,
            },
        )

    @app.exception_handler(InvalidStatusTransitionError)
    async def invalid_transition_handler(
        _request: Request,
        exc: InvalidStatusTransitionError,
    ) -> JSONResponse:
        """Transicao de status invalida -> 409 Conflict."""
        return JSONResponse(
            status_code=409,
            content={
                "error": "INVALID_STATUS_TRANSITION",
                "message": str(exc),
                "status_code": 409,
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        _request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        """
        Qualquer outro erro de dominio -> 422 Unprocessable Entity.
        Handler generico como fallback para erros de dominio nao mapeados.
        """
        return JSONResponse(
            status_code=422,
            content={
                "error": "DOMAIN_ERROR",
                "message": str(exc),
                "status_code": 422,
            },
        )

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(
        _request: Request,
        exc: FileNotFoundError,
    ) -> JSONResponse:
        """Objeto nao encontrado no S3 -> 404."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "STORAGE_OBJECT_NOT_FOUND",
                "message": str(exc),
                "status_code": 404,
            },
        )
