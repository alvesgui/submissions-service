# Submissions Service

Sistema completo para registro e correção assíncrona de respostas discursivas.

## Estrutura

```
submissions-service/
├── backend/   # API REST + Worker (Python, FastAPI, PostgreSQL, SQS, S3)
└── frontend/  # Interface web (React, TypeScript, Tailwind CSS)
```

## Como rodar

### Backend
```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install uv
uv pip install -e ".[dev]"
cp .env.example .env
make up-infra   # sobe Postgres + LocalStack
make migrate    # aplica migrations
make run-api    # API em http://localhost:8000
make run-worker # worker em outro terminal
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # ou crie com: echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev   # http://localhost:5173
```

## Documentação

- [Backend — arquitetura, testes, AWS](./backend/README.md)
- [Frontend — stack e componentes](./frontend/README.md)
