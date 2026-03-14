import type {
  CreateSubmissionRequest,
  CreateSubmissionResponse,
  ListSubmissionsResponse,
  Submission,
} from '../types/submission'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body?.detail ?? `HTTP ${res.status}`)
  }

  return res.json() as Promise<T>
}

export const submissionsApi = {
  create(data: CreateSubmissionRequest): Promise<CreateSubmissionResponse> {
    return request('/api/v1/submissions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  list(studentId: string, limit = 20, offset = 0): Promise<ListSubmissionsResponse> {
    const params = new URLSearchParams({
      student_id: studentId,
      limit: String(limit),
      offset: String(offset),
    })
    return request(`/api/v1/submissions?${params}`)
  },

  getById(id: string): Promise<Submission> {
    return request(`/api/v1/submissions/${id}`)
  },
}