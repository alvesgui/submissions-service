
-- Schema: Corrections Service
-- PostgreSQL 16

-- Enable UUID generation (fallback, primary is ULID via app)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum: submission status
CREATE TYPE submission_status AS ENUM (
    'PENDING',      -- Job criado, aguardando processamento na fila
    'PROCESSING',   -- Worker consumiu e está corrigindo
    'COMPLETED',    -- Correção concluída com sucesso
    'FAILED'        -- Falha no processamento (max retries atingido)
);

-- Table: submissions
CREATE TABLE IF NOT EXISTS submissions (
    -- ULID como PK: ordenável cronologicamente, URL-safe, sem colisão distribuída
    id              VARCHAR(26)         NOT NULL,
    student_id      VARCHAR(255)        NOT NULL,

    -- Referência ao objeto no S3/MinIO (ex: "submissions/2024/01/abc123.txt")
    s3_key          VARCHAR(1024)       NOT NULL,

    -- Status do job de correção
    status          submission_status   NOT NULL    DEFAULT 'PENDING',

    -- Nota resultante da correção (0.0 a 10.0). NULL enquanto PENDING/PROCESSING
    score           NUMERIC(4, 2)       NULL
                        CONSTRAINT score_range CHECK (score IS NULL OR (score >= 0 AND score <= 10)),

    -- Feedback textual da correção (opcional)
    feedback        TEXT                NULL,

    -- Número de tentativas de processamento (para retry logic)
    retry_count     SMALLINT            NOT NULL    DEFAULT 0,

    -- Metadados temporais
    created_at      TIMESTAMPTZ         NOT NULL    DEFAULT NOW(),
    updated_at      TIMESTAMPTZ         NOT NULL    DEFAULT NOW(),

    CONSTRAINT submissions_pkey PRIMARY KEY (id)
);

-- Indexes

-- Consultas por aluno (GET /submissions?student_id=abc)
CREATE INDEX IF NOT EXISTS idx_submissions_student_id
    ON submissions (student_id);

-- Consultas por aluno ordenadas por data (paginação)
CREATE INDEX IF NOT EXISTS idx_submissions_student_id_created_at
    ON submissions (student_id, created_at DESC);

-- Consultas por status (worker busca PENDING, monitoramento busca FAILED)
CREATE INDEX IF NOT EXISTS idx_submissions_status
    ON submissions (status)
    WHERE status IN ('PENDING', 'PROCESSING', 'FAILED');

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_submissions_updated_at
    BEFORE UPDATE ON submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
