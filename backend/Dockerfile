# Base
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Builder
FROM base AS builder

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system --no-dev .

# Development
FROM base AS development

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system .

COPY . .

# Production
FROM base AS production

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Cria usuário não-root para produção
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup src/ ./src/
COPY --chown=appuser:appgroup worker/ ./worker/
COPY --chown=appuser:appgroup migrations/ ./migrations/
COPY --chown=appuser:appgroup alembic.ini .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.adapters.inbound.http.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
