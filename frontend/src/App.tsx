import { useState } from 'react'
import type { Submission } from './types/submission'
import SubmissionForm from './components/SubmissionForm'
import SubmissionList from './components/SubmissionList'
import SubmissionDetail from './components/SubmissionDetail'

type View =
  | { name: 'list'; studentId: string }
  | { name: 'form'; studentId: string }
  | { name: 'detail'; submission: Submission }

export default function App() {
  const [view, setView] = useState<View>({ name: 'list', studentId: '' })

  function goToList(studentId: string) {
    setView({ name: 'list', studentId })
  }

  function goToForm(studentId: string) {
    setView({ name: 'form', studentId })
  }

  function goToDetail(submission: Submission) {
    setView({ name: 'detail', submission })
  }

  return (
    <div className="min-h-screen bg-[#f1f5f9]">
      <header className="border-b border-[#e2e8f0] bg-white px-6 py-4 shadow-sm">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button
            onClick={() => goToList('')}
            className="flex items-center gap-3"
          >
            <div className="w-7 h-7 bg-blue-600 rounded-sm flex items-center justify-center">
              <span className="text-white font-mono font-bold text-xs">SC</span>
            </div>
            <span className="font-mono text-sm text-[#0f172a] tracking-widest uppercase">
              Submission Corrector
            </span>
          </button>

          {view.name !== 'list' && (
            <button
              onClick={() => goToList('')}
              className="font-mono text-xs text-[#94a3b8] hover:text-[#0f172a] transition-colors tracking-wider uppercase"
            >
              ← voltar
            </button>
          )}
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        {view.name === 'list' && (
          <SubmissionList
            initialStudentId={view.studentId}
            onNewSubmission={goToForm}
            onSelectSubmission={goToDetail}
          />
        )}
        {view.name === 'form' && (
          <SubmissionForm
            initialStudentId={view.studentId}
            onSuccess={(studentId) => goToList(studentId)}
            onCancel={() => goToList(view.studentId)}
          />
        )}
        {view.name === 'detail' && (
          <SubmissionDetail
            submission={view.submission}
            onBack={() => goToList(view.submission.student_id)}
          />
        )}
      </main>
    </div>
  )
}