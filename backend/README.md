# Submission Service

Microserviço para registro e correção assíncrona de respostas discursivas, construído com Arquitetura Hexagonal e stack em Python.

## Stack

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn |
| Banco | PostgreSQL 16 (asyncpg) |
| ORM / Migrations | SQLAlchemy 2.x + Alembic |
| Fila | LocalStack SQS (aioboto3) |
| Storage | LocalStack S3 (aioboto3) |
| Worker | Python async consumer |
| Arquitetura | Hexagonal (Ports & Adapters) |
| Qualidade | Ruff + Mypy + Pytest |
| Python | 3.13 |

---

## Pré-requisitos

| Ferramenta | macOS | Linux | Windows |
|---|---|---|---|
| **Docker Desktop** | [download](https://www.docker.com/products/docker-desktop/) | [download](https://www.docker.com/products/docker-desktop/) | [download](https://www.docker.com/products/docker-desktop/) |
| **Python 3.13** | `brew install python@3.13` | `apt install python3.13` ou [pyenv](https://github.com/pyenv/pyenv) | [python.org](https://www.python.org/downloads/) |
| **AWS CLI** | `brew install awscli` | `pip install awscli` | `pip install awscli` |
| **uv** | `pip3 install uv` | `pip3 install uv` | `pip install uv` |

> **Windows:** use o terminal dentro do WSL2 (Ubuntu). Os comandos `make` e os scripts `.sh` não funcionam no PowerShell nativo.

---

## Setup local (primeira vez)

```bash
# 1. Clone o repositório
git clone <repo-url>
cd corrections-service/backend

# 2. Cria e ativa o ambiente virtual
uv venv --python 3.13
source .venv/bin/activate

# 3. Instala todas as dependências (incluindo dev)
uv pip install -e ".[dev]"

# 4. Copia o arquivo de variáveis de ambiente
cp .env.example .env

# 5. Instala os pre-commit hooks
pre-commit install

# 6. Sobe apenas a infraestrutura (Postgres + LocalStack)
make up-infra
# O LocalStack cria automaticamente o bucket S3 e a fila SQS via
# scripts/localstack_init.sh — aguarde ~20s.

# 7. Executa as migrations
make migrate

# 8. Roda a API
make run-api
```

Acesse:
- **API**: http://localhost:8000
- **Documentação OpenAPI**: http://localhost:8000/docs
- **LocalStack**: http://localhost:4566

---

## Variáveis de ambiente

Copie `.env.example` para `.env`. As principais:

| Variável | Descrição | Default dev |
|---|---|---|
| `POSTGRES_USER` | Usuário do banco | `submission_user` |
| `POSTGRES_PASSWORD` | Senha do banco | `submission_pass` |
| `POSTGRES_DB` | Nome do banco | `submission_db` |
| `AWS_ENDPOINT_URL` | Endpoint do LocalStack | `http://localhost:4566` |
| `SQS_QUEUE_URL` | URL da fila SQS | `http://localhost:4566/000000000000/submissions-corrections` |
| `S3_BUCKET` | Nome do bucket | `submissions-texts` |

> Em produção: remova `AWS_ENDPOINT_URL`. O SDK usará o endpoint real da AWS automaticamente via IAM Role.

---

## Comandos úteis

```bash
# Infraestrutura
make up-infra        # Sobe Postgres + LocalStack (modo dev com PyCharm)
make up              # Sobe todos os serviços incluindo API e worker
make down            # Para todos os serviços
make down-v          # Para e remove volumes (slate limpo)

# Banco
make migrate         # Aplica migrations (alembic upgrade head)
make migrate-create MSG="descrição"  # Cria nova migration

# Desenvolvimento
make run-api         # Roda API localmente (requer infra up)
make run-worker      # Roda worker localmente (requer infra up)

# Testes
make test-unit       # Apenas testes unitários (sem Docker)
make test-integration # Sobe containers de teste + roda integração + derruba

# Inspecionar LocalStack (dev)
make ls-queues       # Lista filas SQS
make ls-buckets      # Lista buckets S3
```
---
## Testando via curl

Com a API rodando (`make run-api`), você pode testar todos os endpoints direto no terminal.

### Criar submissão

```bash
curl -s -X POST http://localhost:8000/api/v1/submissions \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "aluno-123",
    "text": "A inteligência artificial transformou profundamente a sociedade contemporânea, impactando desde o mercado de trabalho até as relações interpessoais. Algoritmos de aprendizado de máquina são capazes de processar volumes massivos de dados, identificando padrões que seriam imperceptíveis ao olho humano. No entanto, essa evolução tecnológica levanta questões éticas relevantes sobre privacidade, viés algorítmico e o papel humano na tomada de decisões críticas."
  }' | python3 -m json.tool
```

Resposta esperada (`201 Created`):
```json
{
  "id": "01KKMR7SJ8BBPKR8XYM0Z57MDP",
  "student_id": "aluno-123",
  "s3_key": "submissions/2026/03/01KKMR7SJ8BBPKR8XYM0Z57MDP.txt",
  "status": "PENDING",
  "created_at": "2026-03-14T00:24:21.448732+00:00"
}
```

### Buscar submissão por ID

```bash
curl -s http://localhost:8000/api/v1/submissions/<ID> | python3 -m json.tool
```

Substitua `<ID>` pelo `id` retornado na criação. Resposta após o worker processar:
```json
{
  "id": "01KKMR7SJ8BBPKR8XYM0Z57MDP",
  "student_id": "aluno-123",
  "status": "COMPLETED",
  "score": "7.50",
  "feedback": "Nota final: 7.50\n  Extensao do texto: Insuficiente (0.0/2.5)\n  Riqueza de vocabulario: Excelente (2.5/2.5)\n  Estrutura e pontuacao: Excelente (2.5/2.5)\n  Coesao textual: Excelente (2.5/2.5)\nResultado: APROVADO",
  "retry_count": 0,
  "created_at": "2026-03-14T00:24:21.448732+00:00",
  "updated_at": "2026-03-14T00:24:21.564251+00:00"
}
```

### Listar submissões de um aluno

```bash
curl -s "http://localhost:8000/api/v1/submissions?student_id=aluno-123&limit=10&offset=0" \
  | python3 -m json.tool
```

Resposta:
```json
{
  "items": [ ... ],
  "total": 2,
  "limit": 10,
  "offset": 0
}
```

### Health check

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

> **Dica:** Se preferir tem a opcao visual. O frontend React roda em `http://localhost:5173` (ver `../frontend/README.md`). A documentação interativa OpenAPI está em `http://localhost:8000/docs`.

---

## Testes

O projeto tem dois níveis de testes:

### Unitários

Testam domínio e casos de uso sem dependências externas. Não precisam de Docker.

```bash
pytest -m unit --no-cov -v
```

### Integração

Testam a API e o worker contra containers reais (Postgres + LocalStack). Os recursos AWS (bucket S3 e fila SQS) são criados **automaticamente** pelo script de init do LocalStack ao subir os containers — não é necessário nenhum passo manual.

```bash
# Forma recomendada (sobe containers, testa e derruba)
make test-integration

# Ou com os containers já no ar
docker compose -f docker-compose.test.yml up -d
pytest -m integration --no-cov -v
```

A infraestrutura de teste usa portas isoladas para não conflitar com o ambiente de dev:
- Postgres: `5433` (dev usa `5432`)
- LocalStack: `4567` (dev usa `4566`)

---

## Setup PyCharm

### Interpretador Python

1. `PyCharm → Settings → Project → Python Interpreter`
2. `Add Interpreter → Add Local Interpreter → Virtualenv → Existing`
3. Aponte para: `<projeto>/backend/.venv/bin/python`

### Run Configurations

**API:**
- Script: `uvicorn`
- Parameters: `src.adapters.inbound.http.app:app --reload --host 0.0.0.0 --port 8000`
- Working directory: `$PROJECT_DIR$/backend`
- Env file: `.env`

**Worker:**
- Module: `worker.main`
- Working directory: `$PROJECT_DIR$/backend`
- Env file: `.env`

---

### Fluxo de criação de submissão

```
POST /submissions
      │
      ▼
 CreateSubmission (Use Case)
      ├── S3.upload_text(key, content)      # salva texto
      ├── Repository.save(submission)        # persiste PENDING no Postgres
      └── SQSPublisher.publish(id)           # enfileira para correção

SQS Message
      │
      ▼
 Worker Consumer
      ├── S3.get_text(key)                  # lê texto original
      ├── ProcessSubmission (Use Case)       # aplica 4 critérios de correção
      └── Repository.update(submission)      # persiste COMPLETED + score + feedback
```

### Lógica de correção

4 critérios, cada um vale 2.5 pontos (total 10.0):

| Critério | Como é avaliado |
|---|---|
| **Extensão** | < 50 palavras = 0 pts / 50–149 = 1.25 / 150+ = 2.5 |
| **Vocabulário** | Diversidade de palavras únicas (ratio) |
| **Estrutura** | Uso de pontuação, parágrafos e vírgulas |
| **Coesão** | Presença de conectivos (portanto, além disso, no entanto…) |

Aprovação: nota ≥ 6.0

---

## Arquitetura AWS (produção)

```
                         ┌─────────────────┐
  Client ──────────────▶ │   API Gateway   │ HTTP API
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
           ┌────────────────┐         ┌─────────────────┐
           │ Lambda (Write) │         │  Lambda (Read)  │
           │ POST /submit   │         │  GET /submit    │
           └───────┬────────┘         └────────┬────────┘
                   │                           │
          ┌────────┼────────┐                  │
          │        │        │                  │
          ▼        ▼        ▼                  ▼
        S3      SQS      RDS Proxy ────────▶ RDS
      PutObject  Send    INSERT               SELECT
                Message  (PENDING)
                   │
                   ▼
           ┌───────────────┐
           │ SQS Standard  │  maxReceiveCount=3 → DLQ
           │    Queue      │  VisibilityTimeout=60s
           └───────┬───────┘
                   │ Event Source Mapping
                   ▼
           ┌───────────────┐
           │ Lambda Worker │  batch_size=10
           │  (correction) │
           └───────┬───────┘
                   │
          ┌────────┼──────────────┐
          │        │              │
          ▼        ▼              ▼
        S3      Correção       RDS Proxy
      GetObject  (4 critérios)  UPDATE
                               (COMPLETED
                                score + feedback)

           ┌───────────────┐
           │      DLQ      │ Mensagens que falharam 3x
           └───────┬───────┘
                   │
                   ▼
           CloudWatch Alarm ──▶ SNS ──▶ Slack / PagerDuty
```

### Como funcionaria em produção na AWS

Em produção, o **API Gateway** (HTTP API) expõe os endpoints REST e roteia as requisições para funções **Lambda**. Existe uma Lambda para escrita (`POST /submissions`) e outra para leitura (`GET /submissions/{id}` e `GET /submissions`). Essa separação segue o princípio de responsabilidade única e permite escalar e otimizar memória/timeout de cada função de forma independente.

Quando uma submissão chega, a Lambda de escrita executa três operações em sequência: salva o texto bruto no **S3** (bucket `submissions-texts`), persiste um registro com status `PENDING` no **RDS PostgreSQL** via **RDS Proxy**, e publica uma mensagem na fila **SQS Standard** com o ID da submissão. O uso do RDS Proxy é essencial porque Lambda abre e fecha conexões a cada invocação — sem o proxy, o banco esgotaria o limite de conexões sob carga. O texto vai para o S3 e não para a mensagem SQS porque respostas discursivas podem ser longas, e o SQS tem limite de 256KB por mensagem; a fila trafega apenas o ID.

A fila SQS aciona a **Lambda Worker** via Event Source Mapping com `batch_size=10`, ou seja, a Lambda processa até 10 submissões por invocação. O worker lê o texto do S3, aplica os 4 critérios de correção e atualiza o registro no banco com status `COMPLETED`, nota e feedback. A fila está configurada com `maxReceiveCount=3`: se o processamento falhar 3 vezes (erro de banco, timeout, exceção não tratada), a mensagem é movida automaticamente para a **Dead Letter Queue (DLQ)**, evitando perda silenciosa e loop infinito de reprocessamento.

**Escalabilidade:** Lambda escala automaticamente até 1.000 execuções concorrentes por região sem nenhuma configuração adicional. O SQS Standard tem throughput virtualmente ilimitado. O S3 também escala sem configuração. O único ponto que requer atenção é o banco — daí o RDS Proxy gerenciar o connection pool. Se a ordem de correção por aluno for um requisito, basta substituir o SQS Standard por **SQS FIFO** usando `MessageGroupId = student_id`, garantindo processamento sequencial por aluno sem alterar nenhuma linha de código da aplicação.

**Observabilidade:** toda falha na Lambda Worker aciona um alarme no **CloudWatch**, que notifica via **SNS** (Slack ou PagerDuty). A DLQ funciona como sinal de qualidade: qualquer mensagem que chegue lá indica uma falha que exige investigação. Além disso, o código usa structured logging (JSON), o que permite consultas avançadas no **CloudWatch Logs Insights** — por exemplo, filtrar todos os logs de uma submissão específica pelo `submission_id` em segundos. O **AWS X-Ray** rastreia a cadeia completa `API Gateway → Lambda → SQS → Lambda Worker`, permitindo identificar onde está a latência. Em produção, as Lambdas usam **IAM Roles** com permissões mínimas (least privilege) — nenhuma credencial é armazenada em variáveis de ambiente ou código.

---

## Estrutura do projeto

```
backend/
├── src/
│   ├── config/
│   │   └── settings.py              # Configurações tipadas (Pydantic Settings)
│   ├── core/
│   │   ├── domain/
│   │   │   ├── submission.py        # Entidade principal
│   │   │   ├── submission_status.py # Enum: PENDING / PROCESSING / COMPLETED / FAILED
│   │   │   └── score.py             # Value object de nota
│   │   └── ports/
│   │       ├── inbound/use_cases.py # Interfaces de entrada
│   │       └── outbound/ports.py    # Interfaces de saída (repo, queue, storage)
│   └── adapters/
│       ├── inbound/http/
│       │   ├── app.py               # Factory da aplicação FastAPI
│       │   ├── routers/             # Endpoints REST
│       │   ├── schemas/             # Request/Response (Pydantic)
│       │   ├── dependencies.py      # Injeção de dependências
│       │   └── exception_handlers.py
│       └── outbound/
│           ├── postgres/            # SQLAlchemy models + repositório async
│           ├── sqs/publisher.py     # Publicador SQS (aioboto3)
│           └── s3/storage.py        # Storage S3 (aioboto3)
├── worker/
│   ├── consumer.py                  # Loop de consumo SQS
│   └── main.py                      # Entrypoint do worker
├── migrations/                      # Alembic migrations versionadas
├── tests/
│   ├── unit/                        # 74 testes — domínio e casos de uso
│   └── integration/                 # 21 testes — API + worker contra containers reais
├── scripts/
│   ├── localstack_init.sh           # Cria recursos AWS no LocalStack (dev)
│   └── localstack_init_test.sh      # Cria recursos AWS no LocalStack (teste)
├── docker-compose.yml               # Infra de desenvolvimento
├── docker-compose.test.yml          # Infra isolada para testes de integração
├── schema.sql                       # DDL PostgreSQL
├── pyproject.toml                   # Dependências + config ruff/mypy/pytest
└── Makefile                         # Comandos do projeto
```