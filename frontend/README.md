# Submission Corrector — Frontend

Interface web para envio e acompanhamento de correções de respostas discursivas.

## Stack

| Camada | Tecnologia |
|---|---|
| Framework | React 19 + Vite 6 |
| Linguagem | TypeScript |
| Estilo | Tailwind CSS v4 |
| Tipografia | DM Sans + DM Mono (Google Fonts) |

---

## Pré-requisitos

- **Node.js** 18+ — [nodejs.org](https://nodejs.org)
- **Backend rodando** em `http://localhost:8000` (ver `../backend/README.md`)

---

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # ou crie o .env manualmente (ver abaixo)
npm run dev
```

Acesse: **http://localhost:5173**

---

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do `frontend/`:

```
VITE_API_URL=http://localhost:8000
```

Em produção, aponte para a URL do API Gateway.

---

## Comandos

```bash
npm run dev      # Servidor de desenvolvimento com HMR
npm run build    # Build de produção (gera dist/)
npm run preview  # Preview do build de produção
```

---

## Estrutura

```
src/
├── types/
│   └── submission.ts       # Interfaces e tipos compartilhados
├── api/
│   └── submissions.ts      # Camada de acesso à API
└── components/
    ├── SubmissionForm.tsx   # Formulário de envio
    ├── SubmissionList.tsx   # Lista + busca por student_id
    └── SubmissionDetail.tsx # Nota, status e feedback
```

---

## Funcionalidades

- Busca de submissões por ID do aluno
- Envio de nova resposta discursiva com validação de mínimo de caracteres
- Visualização de nota (0–10), status e feedback detalhado por critério
- Ring de score em SVG com cor dinâmica (verde ≥ 6, azul ≥ 4, vermelho abaixo)
- Paginação da lista de submissões