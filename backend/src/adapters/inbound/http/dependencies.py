from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.outbound.postgres.database import get_session
from src.adapters.outbound.postgres.repositories.submission_repo import (
    PostgresSubmissionRepository,
)
from src.adapters.outbound.s3.storage import S3StorageService
from src.adapters.outbound.sqs.publisher import SQSPublisher
from src.application.use_cases.create_submission import CreateSubmissionUseCaseImpl
from src.application.use_cases.get_submission import GetSubmissionUseCaseImpl
from src.application.use_cases.list_submissions import ListSubmissionsUseCaseImpl
from src.application.use_cases.process_submission import ProcessSubmissionUseCaseImpl
from src.core.ports.inbound.use_cases import (
    CreateSubmissionUseCase,
    GetSubmissionUseCase,
    ListSubmissionsUseCase,
    ProcessSubmissionUseCase,
)

# Infraestrutura


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostgresSubmissionRepository:
    """Cria o repositorio com a session da requisicao atual."""
    return PostgresSubmissionRepository(session=session)


def get_queue() -> SQSPublisher:
    """Cria o publisher SQS."""
    return SQSPublisher()


def get_storage() -> S3StorageService:
    """Cria o servico de storage S3."""
    return S3StorageService()


# Use Cases - Cada use case recebe suas dependencias injetadas automaticamente.



# Fluxo de uma requisicao POST /submissions:
#   get_create_use_case()
#     -> get_repository() -> get_session() -> AsyncSession (do pool)
#     -> get_queue()      -> SQSPublisher
#     -> get_storage()    -> S3StorageService


def get_create_use_case(
    repository: Annotated[PostgresSubmissionRepository, Depends(get_repository)],
    queue: Annotated[SQSPublisher, Depends(get_queue)],
    storage: Annotated[S3StorageService, Depends(get_storage)],
) -> CreateSubmissionUseCase:
    return CreateSubmissionUseCaseImpl(
        repository=repository,
        queue=queue,
        storage=storage,
    )


def get_get_use_case(
    repository: Annotated[PostgresSubmissionRepository, Depends(get_repository)],
) -> GetSubmissionUseCase:
    return GetSubmissionUseCaseImpl(repository=repository)


def get_list_use_case(
    repository: Annotated[PostgresSubmissionRepository, Depends(get_repository)],
) -> ListSubmissionsUseCase:
    return ListSubmissionsUseCaseImpl(repository=repository)


def get_process_use_case(
    repository: Annotated[PostgresSubmissionRepository, Depends(get_repository)],
    storage: Annotated[S3StorageService, Depends(get_storage)],
) -> ProcessSubmissionUseCase:
    return ProcessSubmissionUseCaseImpl(
        repository=repository,
        storage=storage,
    )
