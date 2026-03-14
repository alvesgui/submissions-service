from datetime import UTC, datetime

import aioboto3
from botocore.exceptions import ClientError

from src.config.settings import Settings, get_settings
from src.core.ports.outbound.ports import StorageService


class S3StorageService(StorageService):
    """
    Implementacao do StorageService usando AWS S3.

    Em desenvolvimento: aponta para LocalStack (endpoint_url preenchido).
    Em producao: remove endpoint_url e usa credenciais IAM.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def upload_text(self, key: str, content: str) -> str:
        """
        Faz upload do texto da submissao para o S3.
        """
        session = aioboto3.Session()

        async with session.client(
            "s3",
            region_name=self._settings.aws.region,
            aws_access_key_id=self._settings.aws.access_key_id,
            aws_secret_access_key=self._settings.aws.secret_access_key,
            endpoint_url=self._settings.aws.endpoint_url,
        ) as client:
            await client.put_object(
                Bucket=self._settings.storage.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain; charset=utf-8",
            )

        return key

    async def download_text(self, key: str) -> str:
        """
        Baixa o texto de uma submissao do S3.
        """
        session = aioboto3.Session()

        async with session.client(
            "s3",
            region_name=self._settings.aws.region,
            aws_access_key_id=self._settings.aws.access_key_id,
            aws_secret_access_key=self._settings.aws.secret_access_key,
            endpoint_url=self._settings.aws.endpoint_url,
        ) as client:
            try:
                response = await client.get_object(
                    Bucket=self._settings.storage.bucket,
                    Key=key,
                )
                body = await response["Body"].read()
                return body.decode("utf-8")

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "NoSuchKey":
                    raise FileNotFoundError(f"Objeto nao encontrado no S3: {key}") from e
                raise

    def generate_key(self, submission_id: str) -> str:
        """
        Gera o caminho do objeto no S3 organizado por ano e mes.
        """
        now = datetime.now(UTC)
        return f"submissions/{now.year}/{now.month:02d}/{submission_id}.txt"
