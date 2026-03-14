from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import Settings, get_settings


def create_engine(settings: Settings | None = None):
    """
    Cria o engine assincrono do SQLAlchemy.
    """
    s = settings or get_settings()
    return create_async_engine(
        s.database.async_url,
        pool_size=s.database.pool_size,
        max_overflow=s.database.max_overflow,
        pool_timeout=s.database.pool_timeout,
        # Mostra as queries no log quando DEBUG=True
        echo=s.debug,
    )


def create_session_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """
    Cria a factory de sessions.

    Cada requisicao HTTP recebe uma session propria --
    isso garante isolamento entre requisicoes concorrentes.
    """
    engine = create_engine(settings)
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Session factory global - reutilizada em todas as requisicoes
AsyncSessionFactory = create_session_factory()


async def get_session() -> AsyncGenerator[AsyncSession]:
    """
    Dependency do FastAPI -- injeta uma session por requisicao.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
