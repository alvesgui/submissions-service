import type { Submission, SubmissionStatus } from '../types/submission'

interface Props {
  submission: Submission
  onBack: () => void
}

const STATUS_LABEL: Record<SubmissionStatus, string> = {
  pending:    'Pendente',
  processing: 'Processando',
  completed:  'Corrigido',
  failed:     'Falhou',
}

const STATUS_COLOR: Record<SubmissionStatus, string> = {
  pending:    'text-[#64748b] border-[#cbd5e1] bg-slate-50',
  processing: 'text-blue-600 border-blue-200 bg-blue-50',
  completed:  'text-emerald-600 border-emerald-200 bg-emerald-50',
  failed:     'text-red-600 border-red-200 bg-red-50',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function ScoreRing({ score }: { score: number }) {
  const max         = 10
  const radius      = 40
  const stroke      = 4
  const normalised  = Math.min(Math.max(score, 0), max)
  const circumference = 2 * Math.PI * radius
  const progress    = (normalised / max) * circumference
  const color       = score >= 6 ? '#059669' : score >= 4 ? '#2563eb' : '#dc2626'

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative w-24 h-24">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 96 96">
          <circle cx="48" cy="48" r={radius} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
          <circle
            cx="48" cy="48" r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${progress} ${circumference}`}
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-2xl font-medium text-[#0f172a]">
            {score.toFixed(1)}
          </span>
          <span className="font-mono text-xs text-[#94a3b8]">/ 10</span>
        </div>
      </div>
      <span className="font-mono text-xs tracking-widest uppercase" style={{ color }}>
        {score >= 6 ? 'Aprovado' : 'Reprovado'}
      </span>
    </div>
  )
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-[#f1f5f9] last:border-0">
      <span className="font-mono text-xs text-[#94a3b8] tracking-widest uppercase w-28 shrink-0 pt-0.5">
        {label}
      </span>
      <span className="font-mono text-xs text-[#0f172a] break-all">{value}</span>
    </div>
  )
}

export default function SubmissionDetail({ submission}: Props) {
  const status    = submission.status.toLowerCase() as SubmissionStatus
  const isPending = status === 'pending' || status === 'processing'

  return (
    <div>
      <div className="mb-10">
        <p className="font-mono text-xs text-blue-600 tracking-widest uppercase mb-2">
          Detalhe
        </p>
        <h1 className="text-2xl font-light text-[#0f172a] tracking-tight">
          Resultado da correção
        </h1>
      </div>

      <div className="space-y-6">
        <div className="bg-white border border-[#e2e8f0] rounded-sm p-8 shadow-sm">
          {isPending ? (
            <div className="flex flex-col items-center gap-3 py-4">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="font-mono text-xs text-[#64748b] tracking-widest uppercase">
                Aguardando correção...
              </p>
              <p className="font-mono text-xs text-[#94a3b8] text-center max-w-xs">
                O worker processa a fila de forma assíncrona. Volte em instantes.
              </p>
            </div>
          ) : status === 'failed' ? (
            <div className="flex flex-col items-center gap-3 py-4">
              <span className="text-2xl text-red-500">✕</span>
              <p className="font-mono text-xs text-red-600 tracking-widest uppercase">
                Falha no processamento
              </p>
              <p className="font-mono text-xs text-[#94a3b8]">
                Tentativas: {submission.retry_count}
              </p>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-center gap-8">
              {submission.score !== null && (
                <ScoreRing score={Number(submission.score)} />
              )}
              <div className="flex-1 space-y-4 w-full">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-xs text-[#94a3b8] tracking-widest uppercase w-16">
                    Status
                  </span>
                  <span className={`font-mono text-xs border rounded-sm px-2 py-0.5 ${STATUS_COLOR[status]}`}>
                    {STATUS_LABEL[status]}
                  </span>
                </div>
                {submission.feedback && (
                  <div>
                    <p className="font-mono text-xs text-[#94a3b8] tracking-widest uppercase mb-3">
                      Feedback
                    </p>
                    <p className="text-sm text-[#334155] leading-relaxed whitespace-pre-line">
                      {submission.feedback}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="bg-white border border-[#e2e8f0] rounded-sm px-6 py-2 shadow-sm">
          <MetaRow label="ID"         value={submission.id} />
          <MetaRow label="Aluno"      value={submission.student_id} />
          <MetaRow label="Criado em"  value={formatDate(submission.created_at)} />
          <MetaRow label="Atualizado" value={formatDate(submission.updated_at)} />
          <MetaRow label="S3 Key"     value={submission.s3_key} />
        </div>
      </div>
    </div>
  )
}