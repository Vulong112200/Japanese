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
  verified_by: 'ai' | 'user' | 'pending_user' | null
  dictionary_form: string | null
  review_notes: string | null
  archived: number
  issue_count?: number
}

export interface VocabDetail extends Vocab {
  raw: RawRecord[]
  issues: Issue[]
  sources: Source[]
  history: { action: string; note: string | null; acted_at: string; before_json: string | null; after_json: string | null }[]
}

export type SrsEntity = 'vocabulary' | 'grammar' | 'kanji' | 'number'

export interface Card {
  card_id: number
  entity_type: SrsEntity
  entity_id: string
  direction: 'jp_vi' | 'vi_jp'
  status: string
  interval_days: number
  reps: number
  review_count: number
  meaning_vi: string
  verification_status: Status
  lesson_number?: number | null
  han_viet?: string | null
  // vocabulary
  word?: string
  reading?: string
  romaji?: string | null
  example_jp?: string | null
  example_romaji?: string | null
  example_vi?: string | null
  deck?: string
  // number (ADR-029)
  jp?: string
  note_vi?: string | null
  category_vi?: string
  alt_readings?: string[] | null
  // grammar
  pattern?: string
  grammar_name_vi?: string | null
  formation?: string
  examples?: { jp: string; romaji?: string; vi: string }[]
  // kanji
  kanji?: string
  onyomi?: string[]
  kunyomi?: string[]
  example_words?: { word: string; reading: string; meaning_vi: string }[]
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
  grammar_by_status: Record<string, number>
  kanji_by_status: Record<string, number>
  cards_by_entity: Record<SrsEntity, Record<string, number>>
  due_by_entity: Partial<Record<SrsEntity, number>>
  weak_grammar_points: { grammar_id: string; pattern: string | null; total: number; correct: number; accuracy: number | null }[]
  exam: {
    attempts_submitted: number
    mistakes_pending: number
    bank_questions: number
    last: { attempt_id: string; title: string; mode: string; submitted_at: string; accuracy: number | null; correct: number; total: number } | null
  }
  daily_goal: number
  done_today: number
  study_seconds_today: number
  recommendations: Recommendation[]
}

export interface Recommendation { kind: string; title: string; reason: string; href?: string; start?: AttemptStart }

export interface Analytics {
  daily: { date: string; reviews: number; reviews_correct: number; answers: number; answers_correct: number; seconds: number }[]
  study_seconds_total: number
  study_seconds_period: number
  srs_retention: Partial<Record<SrsEntity, { reviews: number; remembered: number; retention: number }>>
  attempts: { attempt_id: string; title: string; mode: string; submitted_at: string; accuracy: number | null; total: number; by_section: Record<string, number | null> }[]
  by_section: Record<string, Bucket>
  by_mondai: (Bucket & { section: Section; mondai_no: number | null; mondai_type: string | null })[]
  weak_grammar_points: Dashboard['weak_grammar_points']
  repeated_mistakes: { question_id: string; wrong: number; section: Section; mondai_type: string | null; question_text: string | null; grammar_id: string | null; grammar_pattern: string | null }[]
}

// ---------- mock exam ----------
export type Section = 'vocabulary' | 'grammar_reading' | 'listening'

export interface ExamQuestion {
  question_id: string
  exam_id: string
  section: Section
  section_id: string
  mondai_no: number | null
  mondai_type: string | null
  number: number | null
  question_text: string | null
  instruction: string | null
  passage_id: string | null
  options: { option_id: string; text: string | null; image_asset_id?: string }[]
  answer_type: string
  audio_asset_id: string | null
  image_asset_id: string | null
  explanation_origin: string | null
  verification_status: Status
  lesson_number: number | null
  extra: {
    target?: string; star_position?: number; options_are_glyph_images?: boolean; options_are_pictures?: boolean
    options_audio_only?: boolean; has_illustration?: boolean
    option_explanations?: Record<string, string>; expected_sequence?: unknown; expected_sequence_note?: string
    grammar_id?: string; grammar_pattern?: string
    audio_start?: number; audio_end?: number; passage_translation_vi?: string
  }
  // only after submission (exam) or after answering (practice)
  correct_answer?: string[]
  explanation_vi?: string | null
  transcript?: string | null
}

export interface Bucket { total: number; correct: number; incorrect: number; unanswered: number; accuracy: number | null }

export interface Readiness {
  label: string
  language_knowledge_reading: number | null
  listening: number | null
  total: number | null
  likely_pass: boolean | null
  thresholds: { total: number; language_knowledge_reading: number; listening: number }
  notes: string[]
  disclaimer: string
}

export interface ExamResult extends Bucket {
  by_section: Record<string, Bucket>
  by_mondai: (Bucket & { section: string; mondai_no: number | null; mondai_type: string | null })[]
  listening_accuracy: number | null
  weak_vocabulary_lessons: (Bucket & { lesson_number: number })[]
  weak_grammar_points: (Bucket & { grammar_id: string; pattern: string | null })[]
  per_question: Record<string, 'correct' | 'incorrect' | 'unanswered'>
  readiness: Readiness
}

export interface Attempt {
  attempt_id: string
  exam_id: string | null
  title: string
  mode: 'exam' | 'practice'
  started_at: string
  submitted_at: string | null
  current_section: number
  remaining_sec: number | null
  sections: { section_id: string; section: Section; name: string; duration_sec: number | null; question_ids: string[]; status: 'done' | 'current' | 'upcoming' }[]
  questions: ExamQuestion[]
  passages: Record<string, { passage_id: string; text: string; image_asset_id: string | null }>
  answers: Record<string, { answer: string[] | null; flagged: boolean; is_correct: number | boolean | null }>
  result: ExamResult | null
}

export interface AttemptSummary {
  attempt_id: string; title: string; mode: 'exam' | 'practice'; started_at: string; submitted_at: string | null
  question_count: number; summary: Bucket | null; readiness: Readiness | null
}

export interface ExamOverview {
  exams: { exam_id: string; title: string; exam_type: string; source_type: string; is_official: number; duration_minutes: number | null; verification_status: Status; question_count: number }[]
  bank: { section: Section; mondai_no: number; mondai_type: string; exam_type: string; n: number }[]
  mistakes: number
}

export interface AttemptStart {
  mode: 'exam' | 'practice'
  exam_id?: string
  section?: Section
  mondai_type?: string
  source?: 'all' | 'official' | 'past' | 'generated'
  mistakes_only?: boolean
  grammar_id?: string
  lesson_from?: number   // grammar questions of lessons from..to; 26 = N5 bổ sung
  lesson_to?: number
  topic?: 'numbers'
  limit?: number
  timing?: 'none' | 'original' | 'current' | 'custom'
  time_limit_min?: number
}

export interface GrammarItem {
  id: string
  pattern: string
  lesson_number: number | null
  grammar_name_vi: string | null
  meaning_vi: string
  origin: string
  verification_status: Status
  verified_by: string | null
}

export interface GrammarDetail extends GrammarItem {
  formation: string
  explanation_vi: string | null
  usage: string[]
  restrictions: string[]
  formality: string | null
  similar_patterns: { pattern: string; difference_vi: string }[]
  common_mistakes: string[]
  examples: { jp: string; hiragana?: string; romaji?: string; vi: string }[]
  handbook_refs: string[]
  handbook_errors: { quote: string; problem_vi: string; correction_vi: string }[]
  level_note: string | null
  source_ids: string[]
  issues: Issue[]
}

export interface KanjiItem {
  id: string
  kanji: string
  han_viet: string
  meaning_vi: string
  onyomi: string[]
  kunyomi: string[]
  stroke_count: number
  example_words: { vocab_id: string | null; word: string; reading: string; meaning_vi: string }[]
  verification_status: Status
  verified_by: string | null
}

export interface KaiwaItem {
  id: string
  topic: string
  title_vi: string
  situation_vi: string | null
  line_count: number
  verification_status: Status
  verified_by: string | null
}

export interface KaiwaDetail extends KaiwaItem {
  origin: string
  lines: { speaker: string; jp: string; hiragana: string; vi: string }[]
  vocab: { ref: string; id: string; word: string; reading: string; meaning_vi: string }[]
  grammar: { id: string; pattern: string }[]
  issues: Issue[]
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
  analytics: () => req<Analytics>('/stats/analytics'),
  saveSettings: (s: { daily_goal: number }) => req<{ daily_goal: number }>('/settings', { method: 'PUT', body: JSON.stringify(s) }),
  vocab: (p: Record<string, string | number | undefined>) => req<{ total: number; items: Vocab[] }>(`/vocabulary?${qs(p)}`),
  decks: () => req<{ deck: string; lesson_number: number | null; n: number }[]>('/vocabulary/decks'),
  vocabItem: (id: string) => req<VocabDetail>(`/vocabulary/${id}`),
  archive: (id: string) => req<{ archived: boolean }>(`/vocabulary/${id}/archive`, { method: 'POST' }),
  due: (p: Record<string, string | number | undefined | null>) => req<Card[]>(`/srs/due?${qs(p)}`),
  cram: (p: Record<string, string | number | undefined | null>) => req<Card[]>(`/srs/cram?${qs(p)}`),
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
  grammar: (q?: string, lesson?: number) => req<GrammarItem[]>(`/grammar?${qs({ q, lesson })}`),
  grammarItem: (id: string) => req<GrammarDetail>(`/grammar/${id}`),
  numbers: () => req<NumberCategory[]>('/numbers'),
  kanji: () => req<KanjiItem[]>('/kanji'),
  kaiwa: (topic?: string) => req<KaiwaItem[]>(`/kaiwa?${qs({ topic })}`),
  kaiwaItem: (id: string) => req<KaiwaDetail>(`/kaiwa/${id}`),
  backupUrl: '/api/backup',
  restore: (file: File) => req<{ restored: boolean; pre_restore_backup: string | null; counts: Record<string, number> }>(
    '/restore', { method: 'POST', body: file }),
  exams: () => req<ExamOverview>('/exams'),
  attempts: () => req<AttemptSummary[]>('/attempts'),
  attempt: (id: string) => req<Attempt>(`/attempts/${id}`),
  startAttempt: (body: AttemptStart) => req<Attempt>('/attempts', { method: 'POST', body: JSON.stringify(body) }),
  saveAnswer: (id: string, qid: string, answer: string[] | null, flagged: boolean) =>
    req<{ question_id: string; is_correct?: boolean; question?: ExamQuestion }>(`/attempts/${id}/answers/${qid}`,
      { method: 'PUT', body: JSON.stringify({ answer, flagged }) }),
  advance: (id: string) => req<Attempt>(`/attempts/${id}/advance`, { method: 'POST' }),
  submit: (id: string) => req<Attempt>(`/attempts/${id}/submit`, { method: 'POST' }),
}

export interface NumberItem {
  id: string
  category: string
  jp: string
  reading: string
  romaji: string | null
  meaning_vi: string
  irregular: number
  alt_readings?: string[] | null
  note_vi?: string | null
  example_jp: string
  example_vi: string
  verification_status: Status
}

export interface NumberCategory { key: string; title_vi: string; rule_vi: string; items: NumberItem[] }
