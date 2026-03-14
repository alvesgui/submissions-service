import { useState } from 'react'
import { submissionsApi } from '../api/submissions'

interface Props {
  initialStudentId: string
  onSuccess: (studentId: string) => void
  onCancel: () => void
}

const MIN_CHARS = 50

export default function SubmissionForm({ initialStudentId, onSuccess, onCancel }: Props) {
  const [studentId, setStudentId] = useState(initialStudentId)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const charCount = text.trim().length
  const isValid = studentId.trim().length > 0 && charCount >= MIN_CHARS

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!isValid) return
    setLoading(true)
    setError(null)
    try {
      await submissionsApi.create({ student_id: studentId.trim(), text: text.trim() })
      onSuccess(studentId.trim())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao enviar submissão')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-10">
        <p className="font-mono text-xs text-blue-600 tracking-widest uppercase mb-2">
          Nova submissão
        </p>
        <h1 className="text-2xl font-light text-[#0f172a] tracking-tight">
          Enviar resposta para correção
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-mono text-xs text-[#64748b] tracking-widest uppercase mb-2">
            ID do aluno
          </label>
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            placeholder="ex: aluno-123"
            disabled={loading}
            className="
              w-full bg-white border border-[#e2e8f0] rounded-sm
              px-4 py-3 font-mono text-sm text-[#0f172a]
              placeholder:text-[#cbd5e1]
              focus:outline-none focus:border-blue-500
              disabled:opacity-50 transition-colors
            "
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="font-mono text-xs text-[#64748b] tracking-widest uppercase">
              Resposta discursiva
            </label>
            <span className={`font-mono text-xs ${charCount >= MIN_CHARS ? 'text-blue-600' : 'text-[#94a3b8]'}`}>
              {charCount} / {MIN_CHARS} mín.
            </span>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Digite a resposta discursiva aqui..."
            rows={10}
            disabled={loading}
            className="
              w-full bg-white border border-[#e2e8f0] rounded-sm
              px-4 py-3 font-mono text-sm text-[#0f172a] leading-relaxed
              placeholder:text-[#cbd5e1] resize-none
              focus:outline-none focus:border-blue-500
              disabled:opacity-50 transition-colors
            "
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-sm px-4 py-3">
            <p className="font-mono text-xs text-red-600">{error}</p>
          </div>
        )}

        <div className="flex items-center gap-4 pt-2">
          <button
            type="submit"
            disabled={!isValid || loading}
            className="
              bg-blue-600 text-white font-mono text-xs tracking-widest uppercase
              px-6 py-3 rounded-sm
              hover:bg-blue-700 disabled:opacity-30 disabled:cursor-not-allowed
              transition-colors
            "
          >
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="font-mono text-xs text-[#94a3b8] hover:text-[#0f172a] tracking-widest uppercase transition-colors disabled:opacity-30"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}