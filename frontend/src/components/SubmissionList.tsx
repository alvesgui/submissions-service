import { useState, useEffect, useCallback } from 'react'
import type { Submission, SubmissionStatus } from '../types/submission'
import { submissionsApi } from '../api/submissions'

interface Props {
  initialStudentId: string
  onNewSubmission: (studentId: string) => void
  onSelectSubmission: (submission: Submission) => void
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

export default function SubmissionList({ initialStudentId, onNewSubmission, onSelectSubmission }: Props) {
  const [studentId, setStudentId]     = useState(initialStudentId)
  const [query, setQuery]             = useState(initialStudentId)
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [total, setTotal]             = useState(0)
  const [offset, setOffset]           = useState(0)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState<string | null>(null)
  const [searched, setSearched]       = useState(false)

  const LIMIT = 10

  const fetchSubmissions = useCallback(async (sid: string, off: number) => {
    if (!sid.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await submissionsApi.list(sid.trim(), LIMIT, off)
      setSubmissions(data.items)
      setTotal(data.total)
      setSearched(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar submissões')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (initialStudentId) fetchSubmissions(initialStudentId, 0)
  }, [initialStudentId, fetchSubmissions])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setStudentId(query)
    setOffset(0)
    fetchSubmissions(query, 0)
  }

  function handlePrev() {
    const newOffset = Math.max(0, offset - LIMIT)
    setOffset(newOffset)
    fetchSubmissions(studentId, newOffset)
  }

  function handleNext() {
    const newOffset = offset + LIMIT
    setOffset(newOffset)
    fetchSubmissions(studentId, newOffset)
  }

  const totalPages  = Math.ceil(total / LIMIT)
  const currentPage = Math.floor(offset / LIMIT) + 1
  const hasPrev     = offset > 0
  const hasNext     = offset + LIMIT < total

  return (
    <div>
      <div className="mb-10">
        <p className="font-mono text-xs text-blue-600 tracking-widest uppercase mb-2">
          Correções
        </p>
        <h1 className="text-2xl font-light text-[#0f172a] tracking-tight">
          Submissões do aluno
        </h1>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ID do aluno..."
          className="
            flex-1 bg-white border border-[#e2e8f0] rounded-sm
            px-4 py-3 font-mono text-sm text-[#0f172a]
            placeholder:text-[#cbd5e1]
            focus:outline-none focus:border-blue-500
            transition-colors
          "
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="
            bg-blue-600 text-white font-mono text-xs tracking-widest uppercase
            px-6 py-3 rounded-sm
            hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed
            transition-colors whitespace-nowrap
          "
        >
          {loading ? 'Buscando...' : 'Buscar'}
        </button>
        <button
          type="button"
          onClick={() => onNewSubmission(query.trim())}
          className="
            border border-[#e2e8f0] bg-white text-[#0f172a] font-mono text-xs tracking-widest uppercase
            px-6 py-3 rounded-sm
            hover:border-blue-400 hover:text-blue-600
            transition-colors whitespace-nowrap
          "
        >
          + Nova Submissao
        </button>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-sm px-4 py-3 mb-6">
          <p className="font-mono text-xs text-red-600">{error}</p>
        </div>
      )}

      {!searched && !loading && (
        <div className="border border-dashed border-[#e2e8f0] rounded-sm py-16 text-center bg-white">
          <p className="font-mono text-xs text-[#94a3b8] tracking-widest uppercase">
            Digite um ID de aluno para buscar
          </p>
        </div>
      )}

      {searched && !loading && submissions.length === 0 && (
        <div className="border border-dashed border-[#e2e8f0] rounded-sm py-16 text-center bg-white">
          <p className="font-mono text-xs text-[#64748b] tracking-widest uppercase mb-3">
            Nenhuma submissão encontrada
          </p>
          <button
            onClick={() => onNewSubmission(studentId)}
            className="font-mono text-xs text-blue-600 hover:text-blue-700 tracking-widest uppercase transition-colors"
          >
            + Criar primeira submissão
          </button>
        </div>
      )}

      {submissions.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="font-mono text-xs text-[#64748b]">
              {total} submiss{total !== 1 ? 'ões' : 'ão'} —{' '}
              <span className="text-[#0f172a]">{studentId}</span>
            </p>
            {totalPages > 1 && (
              <p className="font-mono text-xs text-[#64748b]">
                {currentPage} / {totalPages}
              </p>
            )}
          </div>

          <div className="bg-white border border-[#e2e8f0] rounded-sm overflow-hidden">
            <div className="grid grid-cols-[1fr_120px_80px_140px] gap-4 px-4 py-3 border-b border-[#e2e8f0] bg-[#f8fafc]">
              {['ID', 'Status', 'Nota', 'Data'].map((h) => (
                <span key={h} className="font-mono text-xs text-[#94a3b8] tracking-widest uppercase">
                  {h}
                </span>
              ))}
            </div>

            <div className="divide-y divide-[#f1f5f9]">
              {submissions.map((s) => {
                const st = s.status.toLowerCase() as SubmissionStatus
                return (
                  <button
                    key={s.id}
                    onClick={() => onSelectSubmission(s)}
                    className="w-full grid grid-cols-[1fr_120px_80px_140px] gap-4 px-4 py-4 text-left hover:bg-[#f8fafc] transition-colors group"
                  >
                    <span className="font-mono text-xs text-[#94a3b8] group-hover:text-[#0f172a] transition-colors truncate">
                      {s.id}
                    </span>
                    <span className={`font-mono text-xs border rounded-sm px-2 py-0.5 w-fit ${STATUS_COLOR[st]}`}>
                      {STATUS_LABEL[st]}
                    </span>
                    <span className="font-mono text-sm text-[#0f172a] font-medium">
                      {s.score !== null ? Number(s.score).toFixed(1) : '—'}
                    </span>
                    <span className="font-mono text-xs text-[#64748b]">
                      {formatDate(s.created_at)}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-3 mt-6 pt-6 border-t border-[#e2e8f0]">
              <button
                onClick={handlePrev}
                disabled={!hasPrev || loading}
                className="font-mono text-xs text-[#64748b] hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed tracking-widest uppercase transition-colors"
              >
                ← Anterior
              </button>
              <button
                onClick={handleNext}
                disabled={!hasNext || loading}
                className="font-mono text-xs text-[#64748b] hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed tracking-widest uppercase transition-colors"
              >
                Próxima →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}