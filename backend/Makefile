.PHONY: help install setup up down logs test test-unit test-integration lint format typecheck migrate shell clean

# Colors
CYAN  := \033[0;36m
RESET := \033[0m

help: ## Show this help
	@echo ""
	@echo "$(CYAN)Submission Service — Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# Setup
install: ## Install all Python dependencies (including dev)
	pip install uv
	uv pip install -e ".[dev]"

setup: install ## Full setup: install deps + copy .env + pre-commit hooks
	@test -f .env || cp .env.example .env && echo "✅ .env created from .env.example"
	pre-commit install
	@echo "✅ Setup complete. Run 'make up' to start services."

# Docker
up: ## Start all services (postgres, localstack, api, worker)
	docker compose up -d
	@echo "✅ Services running:"
	@echo "   API:         http://localhost:8000"
	@echo "   API Docs:    http://localhost:8000/docs"
	@echo "   LocalStack:  http://localhost:4566"

up-infra: ## Start only infrastructure (no api/worker — for local dev with PyCharm)
	docker compose up -d postgres localstack
	@echo "✅ Infra ready:"
	@echo "   Postgres:       localhost:5432"
	@echo "   LocalStack:     http://localhost:4566"

ls-queues: ## List SQS queues in LocalStack
	AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
	aws --endpoint-url=http://localhost:4566 --region us-east-1 sqs list-queues

ls-buckets: ## List S3 buckets in LocalStack
	AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
	aws --endpoint-url=http://localhost:4566 --region us-east-1 s3 ls

down: ## Stop all services
	docker compose down

down-v: ## Stop all services and remove volumes (clean slate)
	docker compose down -v

logs: ## Tail logs from all services
	docker compose logs -f

logs-api: ## Tail API logs
	docker compose logs -f api

logs-worker: ## Tail worker logs
	docker compose logs -f worker

# Database
migrate: ## Run Alembic migrations
	python -m alembic upgrade head

migrate-create: ## Create new migration (usage: make migrate-create MSG="add column")
	python -m alembic revision --autogenerate -m "$(MSG)"

migrate-rollback: ## Rollback last migration
	python -m alembic downgrade -1

# Development
run-api: ## Run API locally (requires infra up)
	python -m uvicorn src.adapters.inbound.http.app:app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run worker locally (requires infra up)
	python -m worker.main

# Tests
test: ## Run all tests (unit + integration)
	pytest

test-unit: ## Run only unit tests (no docker needed)
	pytest -m unit --no-cov

test-integration: ## Run integration tests (requires test docker services)
	docker compose -f docker-compose.test.yml up -d
	pytest -m integration
	docker compose -f docker-compose.test.yml down

test-watch: ## Run tests in watch mode
	ptw -- -m unit

# Code Quality
lint: ## Run ruff linter
	ruff check src worker tests

format: ## Format code with ruff
	ruff format src worker tests
	ruff check --fix src worker tests

typecheck: ## Run mypy type checker
	mypy src worker

quality: lint typecheck ## Run all quality checks

# Utils
shell: ## Open shell in API container
	docker compose exec api bash

clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache
