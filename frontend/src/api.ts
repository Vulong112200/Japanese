// Thin typed client for the FastAPI backend (/api). All business logic lives server-side.

export type Status = 'raw' | 'extracted' | 'normalized' | 'needs_review' | 'verified' | 'rejected'

export interface Issue {
  issue_id: number
  code: string
  severity: 'error' | 'warning' | 'info'
  message: string
  suggestion: string | null
  origin: 'rule' | 'ai_review' | 'user'
  resolved: number
}

export interface RawRecord {
  raw_id: number
  source_id: string
  locator: string
  content: string
  extraction_method: string
  extracted_at: string
}

export interface Source {
  source_id: string
  source_type: string
  name: string
  location: string | null
  url: string | null
  reliability: string
  purpose: string | null
  size_bytes: number | null
  page_count: number | null
  duration_seconds: number | null
  processing_status: string
  access_status: string | null
  checked_at: string | null
  imported_at: string | null
  record_count: number
  notes: string | null
  error: string | null
}

export interface Vocab {
  id: string
  word: string
  reading: string
  romaji: string | null
  han_viet: string | null
  meaning_vi: string
  part_of_speech: string | null
  verb_group: number | null
  lesson_number: number | null
  deck: string
  topic: string[]
  example_jp: string | null
  example_romaji: string | null
  example_vi: string | null
  source_ids: string[]
  raw_ids: number[]
  verification_status: Status
  review_notes: string | null
  archived: number
  issue_count?: number
}

export interface VocabDetail extends Vocab {
  raw: RawRecord[]
  issues: Issue[]
  sources: Source[]
  history: { action: string; note: string | null; acted_at: string }[]
}

export interface Card {
  card_id: number
  direction: 'jp_vi' | 'vi_jp'
  status: string
  interval_days: number
  reps: number
  review_count: number
  word: string
  reading: string
  romaji: string | null
  han_viet: string | null
  meaning_vi: string
  example_jp: string | null
  example_romaji: string | null
  example_vi: string | null
  lesson_number: number | null
  deck: string
  verification_status: Status
}

export interface Question {
  question_id: string
  section: string
  section_id: string
  mondai_no: number
  mondai_type: string
  number: number
  question_text: string | null
  instruction: string | null
  options: { option_id: string; text: string | null; image_asset_id?: string }[]
  correct_answer: string[]
  extra_json: Record<string, unknown>
  explanation_vi: string | null
  explanation_origin: string | null
  audio_asset_id: string | null
  transcript: string | null
  source_page: number | null
  verification_status: Status
  review_notes: string | null
  issue_count?: number
}

export interface QuestionDetail extends Question {
  issues: Issue[]
  raw: RawRecord[]
  passage: { passage_id: string; text: string; image_asset_id: string | null } | null
  page_asset_id: string | null
}

export interface Dashboard {
  level: string
  vocabulary_by_status: Record<string, number>
  cards_by_status: Record<string, number>
  cards_by_status_vi_jp: Record<string, number>
  due_now: Record<string, number>
  reviews_today: number
  correct_today: number
  streak_days: number
  questions_by_status: Record<string, number>
  sources_by_access: Record<string, number>
  open_issues: Record<string, number>
  weak_lessons: { lesson_number: number | null; deck: string; wrong: number; right: number }[]
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api${path}`, {
    ...init,
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
  })
  if (!r.ok) {
    let msg = `${r.status}`
    try {
      const j = await r.json()
      msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch { /* non-JSON error */ }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

const qs = (p: Record<string, string | number | undefined | null>) =>
  new URLSearchParams(Object.entries(p).filter(([, v]) => v !== undefined && v !== null && v !== '').map(([k, v]) => [k, String(v)])).toString()

export const api = {
  dashboard: () => req<Dashboard>('/stats/dashboard'),
  vocab: (p: Record<string, string | number | undefined>) => req<{ total: number; items: Vocab[] }>(`/vocabulary?${qs(p)}`),
  decks: () => req<{ deck: string; lesson_number: number | null; n: number }[]>('/vocabulary/decks'),
  vocabItem: (id: string) => req<VocabDetail>(`/vocabulary/${id}`),
  archive: (id: string) => req<{ archived: boolean }>(`/vocabulary/${id}/archive`, { method: 'POST' }),
  due: (direction: string, newLimit: number, lesson?: number) =>
    req<Card[]>(`/srs/due?${qs({ direction, new_limit: newLimit, lesson })}`),
  answer: (cardId: number, rating: string) =>
    req<Card>(`/srs/cards/${cardId}/answer`, { method: 'POST', body: JSON.stringify({ rating }) }),
  queue: (entity: string, status?: string, offset = 0) =>
    req<{ total: number; items: (Vocab & Question)[] }>(`/review/queue?${qs({ entity, status, offset, limit: 50 })}`),
  question: (id: string) => req<QuestionDetail>(`/questions/${id}`),
  review: (entity: string, id: string, body: object) =>
    req<VocabDetail & QuestionDetail>(`/review/${entity}/${id}`, { method: 'POST', body: JSON.stringify(body) }),
  sources: (q?: string, sourceType?: string) => req<Source[]>(`/sources?${qs({ q, source_type: sourceType })}`),
  addSource: (body: object) => req<Source>('/sources', { method: 'POST', body: JSON.stringify(body) }),
  scan: () => req<{ files: unknown[] }>('/sources/scan', { method: 'POST' }),
  checkOnline: () => req<unknown[]>('/sources/check-online', { method: 'POST' }),
  reprocess: (id: string) => req<unknown>(`/sources/${id}/reprocess`, { method: 'POST' }),
  assetUrl: (id: string) => `/api/assets/${id}`,
}
