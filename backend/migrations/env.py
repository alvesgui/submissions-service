from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.config.settings import get_settings

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so Alembic can detect changes for autogenerate
from src.adapters.outbound.postgres.models import Base

target_metadata = Base.metadata

# Override sqlalchemy.url com a URL sincrona (psycopg2)
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database.sync_url)


def run_migrations_offline() -> None:
    """Roda migrations sem conexao com o banco (gera SQL apenas)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Roda migrations com conexao real ao banco.
    Usa psycopg2 (sincrono)
    A API usa asyncpg.
    """
    connectable = create_engine(
        settings.database.sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()