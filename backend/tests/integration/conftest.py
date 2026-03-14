import os

import boto3
import pytest
import pytest_asyncio
from botocore.exceptions import ClientError
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.adapters.inbound.http.app import create_app
from src.adapters.inbound.http.dependencies import (
    get_queue,
    get_repository,
    get_storage,
)
from src.adapters.outbound.postgres.database import get_session
from src.adapters.outbound.postgres.models import Base
from src.adapters.outbound.postgres.repositories.submission_repo import (
    PostgresSubmissionRepository,
)
from src.adapters.outbound.s3.storage import S3StorageService
from src.adapters.outbound.sqs.publisher import SQSPublisher
from src.config.settings import (
    AWSSettings,
    DatabaseSettings,
    Settings,
    SQSSettings,
    StorageSettings,
)

# Constantes de teste

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://test_user:test_pass@localhost:5433/test_db",
)
TEST_LOCALSTACK_URL = os.getenv("TEST_LOCALSTACK_URL", "http://localhost:4567")
TEST_BUCKET = "submissions-texts"
TEST_QUEUE = "submissions-corrections"

_AWS_KWARGS = dict(
    endpoint_url=TEST_LOCALSTACK_URL,
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)


def make_test_settings() -> Settings:
    return Settings(
        env="testing",
        debug=False,
        database=DatabaseSettings(
            host="localhost",
            port=5433,
            user="test_user",
            password="test_pass",
            name="test_db",
        ),
        aws=AWSSettings(
            endpoint_url=TEST_LOCALSTACK_URL,
            access_key_id="test",
            secret_access_key="test",
            region="us-east-1",
        ),
        sqs=SQSSettings(
            queue_url=f"{TEST_LOCALSTACK_URL}/000000000000/{TEST_QUEUE}",
        ),
        storage=StorageSettings(
            bucket=TEST_BUCKET,
        ),
    )


# Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return make_test_settings()


@pytest.fixture(scope="session", autouse=True)
def ensure_aws_resources() -> None:
    """Garante que bucket S3 e fila SQS existem no LocalStack de teste."""
    s3 = boto3.client("s3", **_AWS_KWARGS)
    sqs = boto3.client("sqs", **_AWS_KWARGS)

    # S3 bucket
    try:
        s3.create_bucket(Bucket=TEST_BUCKET)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code not in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            raise

    # SQS queue
    try:
        sqs.create_queue(
            QueueName=TEST_QUEUE,
            Attributes={"VisibilityTimeout": "30", "MessageRetentionPeriod": "3600"},
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "QueueAlreadyExists":
            raise


# Engine e Session - cada teste recebe um banco limpo.


@pytest_asyncio.fixture
async def test_engine():
    """Engine por teste: sobe o schema e derruba ao final."""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Session isolada: rollback automático ao final de cada teste."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


# HTTP Client


@pytest_asyncio.fixture
async def test_client(db_session: AsyncSession, test_settings: Settings) -> AsyncClient:
    """
    Client HTTPX com as dependências do FastAPI substituídas pelas de teste.
    Banco, S3 e SQS apontam para os containers de teste criado no docker-compose-test.
    """
    app = create_app()

    app.dependency_overrides[get_session] = lambda: (yield db_session)
    app.dependency_overrides[get_repository] = lambda: PostgresSubmissionRepository(
        session=db_session
    )
    app.dependency_overrides[get_queue] = lambda: SQSPublisher(settings=test_settings)
    app.dependency_overrides[get_storage] = lambda: S3StorageService(settings=test_settings)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
