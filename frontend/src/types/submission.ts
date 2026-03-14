// Volte para:
export type SubmissionStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Submission {
  id: string
  student_id: string
  s3_key: string
  status: SubmissionStatus
  score: number | string | null
  feedback: string | null
  retry_count: number
  created_at: string
  updated_at: string
}

export interface CreateSubmissionRequest {
  student_id: string
  text: string
}

export interface CreateSubmissionResponse {
  id: string
  student_id: string
  status: SubmissionStatus
  created_at: string
}

export interface ListSubmissionsResponse {
  items: Submission[]
  total: number
  limit: number
  offset: number
}