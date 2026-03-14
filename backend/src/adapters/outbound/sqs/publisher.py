import json

import aioboto3

from src.config.settings import Settings, get_settings
from src.core.ports.outbound.ports import QueuePublisher


class SQSPublisher(QueuePublisher):
    """
    Implementacao do QueuePublisher usando AWS SQS.

    Em desenvolvimento: aponta para LocalStack (endpoint_url preenchido).
    Em producao: remove endpoint_url e usa credenciais IAM
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def publish(self, submission_id: str) -> None:
        """
        Publica o ID da submissao na fila SQS.

        A mensagem contem apenas o ID - o script worker busca o estado
        mais recente do banco quando consumir. Isso evita mensagens
        desatualizadas na fila.

        Em producao com fila FIFO, usariamos student_id como
        MessageGroupId para garantir ordem de processamento por aluno.
        """
        session = aioboto3.Session()

        async with session.client(
            "sqs",
            region_name=self._settings.aws.region,
            aws_access_key_id=self._settings.aws.access_key_id,
            aws_secret_access_key=self._settings.aws.secret_access_key,
            endpoint_url=self._settings.aws.endpoint_url,
        ) as client:
            message = json.dumps({"submission_id": submission_id})

            await client.send_message(
                QueueUrl=self._settings.sqs.queue_url,
                MessageBody=message,
            )
