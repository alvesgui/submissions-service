import json
import logging

import aioboto3

from src.adapters.outbound.postgres.database import AsyncSessionFactory
from src.adapters.outbound.postgres.repositories.submission_repo import (
    PostgresSubmissionRepository,
)
from src.adapters.outbound.s3.storage import S3StorageService
from src.application.use_cases.process_submission import ProcessSubmissionUseCaseImpl
from src.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class SQSConsumer:
    """
    Consumidor da fila SQS.

    Responsabilidades:
    - Buscar mensagens da fila em long polling
    - Extrair o submission_id da mensagem
    - Chamar o use case de processamento
    - Confirmar (delete da fila) a mensagem em caso de sucesso
    - Rejeitar (visibility timeout) em caso de falha para retry automatico
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def start(self) -> None:
        """Loop principal"""
        logger.info(
            "Worker iniciado. Aguardando mensagens na fila: %s",
            self._settings.sqs.queue_url,
        )

        session = aioboto3.Session()

        async with session.client(
            "sqs",
            region_name=self._settings.aws.region,
            aws_access_key_id=self._settings.aws.access_key_id,
            aws_secret_access_key=self._settings.aws.secret_access_key,
            endpoint_url=self._settings.aws.endpoint_url,
        ) as client:
            while True:
                await self._poll(client)

    async def _poll(self, client) -> None:
        """
        Busca um lote de mensagens e processa cada uma.
        """
        response = await client.receive_message(
            QueueUrl=self._settings.sqs.queue_url,
            MaxNumberOfMessages=self._settings.worker.batch_size,
            WaitTimeSeconds=self._settings.worker.wait_time_seconds,
            AttributeNames=["ApproximateReceiveCount"],
        )

        messages = response.get("Messages", [])
        if not messages:
            return

        logger.info("Recebidas %d mensagens da fila.", len(messages))

        for message in messages:
            await self._process_message(client, message)

    async def _process_message(self, client, message: dict) -> None:
        """
        Processa uma unica mensagem.

        Fluxo:
        - Extrai submission_id do body
        - Chama o use case de processamento
        - Sucesso: deleta a mensagem da fila
        - Falha: loga o erro e deixa a mensagem voltar para a fila
          (visibility timeout expira e SQS re-entrega automaticamente)
        """
        receipt_handle = message["ReceiptHandle"]

        try:
            body = json.loads(message["Body"])
            submission_id = body["submission_id"]

            logger.info("Processando submissao: %s", submission_id)

            await self._run_use_case(submission_id)

            # Sucesso - remove a mensagem da fila
            await client.delete_message(
                QueueUrl=self._settings.sqs.queue_url,
                ReceiptHandle=receipt_handle,
            )
            logger.info("Submissao processada com sucesso: %s", submission_id)

        except Exception as exc:
            logger.error(
                "Falha ao processar mensagem: %s. Erro: %s",
                message.get("Body"),
                exc,
                exc_info=True,
            )
            # Apos maxReceiveCount(3), vai para a DLQ automaticamente

    async def _run_use_case(self, submission_id: str) -> None:
        """
        Cria as dependencias e executa o use case.
        Cada mensagem tem sua propria session de banco.
        """
        async with AsyncSessionFactory() as session:
            try:
                repository = PostgresSubmissionRepository(session=session)
                storage = S3StorageService(settings=self._settings)

                use_case = ProcessSubmissionUseCaseImpl(
                    repository=repository,
                    storage=storage,
                )

                await use_case.execute(submission_id)
                await session.commit()

            except Exception:
                await session.rollback()
                raise
