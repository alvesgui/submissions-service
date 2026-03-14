import asyncio
import logging
import signal
import sys

from worker.consumer import SQSConsumer

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger("worker")


# Terminar a mensagem atual antes de sair.
_shutdown = asyncio.Event()


def _handle_signal(sig: signal.Signals) -> None:
    logger.info("Sinal %s recebido. Encerrando worker...", sig.name)
    _shutdown.set()


async def main() -> None:
    """
    Ponto de entrada assincrono do worker.

    Registra handlers de sinal e inicia o consumer.
    O worker roda ate receber SIGTERM ou SIGINT.
    """
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, _handle_signal, signal.SIGTERM)
    loop.add_signal_handler(signal.SIGINT, _handle_signal, signal.SIGINT)

    consumer = SQSConsumer()

    consumer_task = asyncio.create_task(consumer.start())
    shutdown_task = asyncio.create_task(_shutdown.wait())

    logger.info("Worker pronto. PID: %s", __import__("os").getpid())

    # Aguarda o primeiro a terminar: shutdown ou erro no consumer
    done, pending = await asyncio.wait(
        {consumer_task, shutdown_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Cancela o que ainda estiver rodando
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    # Se o consumer terminou com erro, propaga
    if consumer_task in done and not consumer_task.cancelled():
        exc = consumer_task.exception()
        if exc:
            logger.error("Worker encerrado com erro: %s", exc, exc_info=exc)
            sys.exit(1)

    logger.info("Worker encerrado com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())
