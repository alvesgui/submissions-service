from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")

    user: str = Field(default="submission_user")
    password: str = Field(default="submission_pass")
    db: str = Field(default="submission_db")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")

    @computed_field  # type: ignore[misc]
    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @computed_field  # type: ignore[misc]
    @property
    def sync_url(self) -> str:
        """Used by Alembic migrations (sync driver)."""
        return (
            f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
        )

class AWSSettings(BaseSettings):
    """
    Configurações AWS compartilhadas entre SQS e S3.

    LocalStack: endpoint_url = http://localhost:4566, credenciais falsas.
    Produção:   endpoint_url = None, credenciais via IAM Role.
    """

    model_config = SettingsConfigDict(env_prefix="AWS_", env_file=".env", extra="ignore")

    region: str = Field(default="us-east-1")
    access_key_id: str = Field(default="test")  # LocalStack aceita qualquer valor
    secret_access_key: str = Field(default="test")  # Em prod: usa IAM Role, não chaves
    # None em produção, o SDK detecta o endpoint automaticamente
    endpoint_url: str | None = Field(default="http://localhost:4566")

    @computed_field  # type: ignore[misc]
    @property
    def is_localstack(self) -> bool:
        return self.endpoint_url is not None and "localhost" in self.endpoint_url

class SQSSettings(BaseSettings):
    """
    Configuração do SQS.

    Em desenvolvimento: aponta para LocalStack (endpoint_url preenchido).
    Em produção AWS: endpoint_url fica None e o SDK usa o endpoint real da AWS.
    """

    model_config = SettingsConfigDict(env_prefix="SQS_", env_file=".env", extra="ignore")

    # URL da fila principal
    queue_url: str = Field(default="http://localhost:4566/000000000000/submissions-corrections")
    # URL da DLQ — para monitoramento e reprocessamento manual
    dlq_url: str = Field(default="http://localhost:4566/000000000000/submissions-corrections-dlq")
    queue_name: str = Field(default="submissions-corrections")
    dlq_name: str = Field(default="submissions-corrections-dlq")

    # Configs de consumo, equivalente ao Lambda Event Source Mapping AWS
    max_messages: int = Field(default=10)  # Batch size (1–10 no SQS real)
    wait_time_seconds: int = Field(default=5)  # Long polling — reduz custo
    visibility_timeout: int = Field(default=60)  # Tempo de processamento esperado

    @computed_field  # type: ignore[misc]
    @property
    def aws_settings(self) -> "AWSSettings":
        return AWSSettings()


class StorageSettings(BaseSettings):
    """
    Configuração do storage S3 (textos das submissões).

    Em desenvolvimento: LocalStack S3 em localhost:4566.
    Em produção: S3 real via IAM Role.
    """

    model_config = SettingsConfigDict(env_prefix="S3_", env_file=".env", extra="ignore")

    bucket: str = Field(default="submissions-texts")


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKER_", env_file=".env", extra="ignore")

    poll_interval_ms: int = Field(default=500)
    max_retries: int = Field(default=3)
    batch_size: int = Field(default=10)
    wait_time_seconds: int = Field(default=20)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: Literal["development", "testing", "production"] = Field(default="development")
    app_name: str = Field(default="submission-service")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    sqs: SQSSettings = Field(default_factory=SQSSettings)
    aws: AWSSettings = Field(default_factory=AWSSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    worker: WorkerSettings = Field(default_factory=WorkerSettings)

    @computed_field  # type: ignore[misc]
    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — injetado via FastAPI Depends."""
    return Settings()
