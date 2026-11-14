import { useEffect, useState } from 'react'
import { api, type Dashboard as D } from '../api'
import { ErrorBox, Loading, Panel } from '../ui'

const CARD_STATUS: [string, string, string][] = [
  ['new', 'Mới', 'bg-slate-300 dark:bg-slate-600'],
  ['learning', 'Đang học', 'bg-sky-500'],
  ['reviewing', 'Đang ôn', 'bg-indigo-500'],
  ['mastered', 'Thuộc', 'bg-emerald-500'],
  ['needs_attention', 'Cần chú ý', 'bg-rose-500'],
]

function Stat({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

function StackBar({ data, total }: { data: Record<string, number>; total: number }) {
  return (
    <div>
      <div className="flex h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="img"
        aria-label={CARD_STATUS.map(([k, l]) => `${l}: ${data[k] ?? 0}`).join(', ')}>
        {CARD_STATUS.map(([k, , c]) => (data[k] ? <div key={k} className={c} style={{ width: `${(data[k] / total) * 100}%` }} /> : null))}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-300">
        {CARD_STATUS.map(([k, l, c]) => (
          <li key={k} className="flex items-center gap-1.5"><span className={`h-2 w-2 rounded-full ${c}`} />{l} <b className="tabular-nums">{data[k] ?? 0}</b></li>
        ))}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  const [d, setD] = useState<D | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.dashboard().then(setD).catch(setErr) }, [])
  if (err) return <ErrorBox error={err} />
  if (!d) return <Loading />

  const vocabTotal = Object.values(d.vocabulary_by_status).reduce((a, b) => a + b, 0)
  const cardTotal = Object.values(d.cards_by_status).reduce((a, b) => a + b, 0) || 1
  const due = (d.due_now.jp_vi ?? 0) + (d.due_now.vi_jp ?? 0)
  const verified = d.vocabulary_by_status.verified ?? 0
  const accuracy = d.reviews_today ? Math.round((d.correct_today / d.reviews_today) * 100) : null

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">Tổng quan · JLPT {d.level}</h1>
          <p className="text-sm text-slate-500">Số liệu lấy trực tiếp từ cơ sở dữ liệu học tập của bạn.</p>
        </div>
        <a href="#/flashcards" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
          {due ? `Ôn ${due} thẻ đến hạn` : 'Học thẻ mới'}
        </a>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Chuỗi ngày học" value={`${d.streak_days} ngày`} />
        <Stat label="Lượt ôn hôm nay" value={d.reviews_today} hint={accuracy !== null ? `Nhớ đúng ${accuracy}%` : 'Chưa ôn hôm nay'} />
        <Stat label="Thẻ đến hạn" value={due} hint={`JP→VI ${d.due_now.jp_vi ?? 0} · VI→JP ${d.due_now.vi_jp ?? 0}`} />
        <Stat label="Từ vựng đã xác minh" value={`${verified}/${vocabTotal}`} hint="Còn lại: học được, có nhãn 'Chưa xác minh'" />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Mức độ thuộc từ vựng (JP→VI)">
          <StackBar data={d.cards_by_status} total={cardTotal} />
          <p className="mt-3 text-xs text-slate-500">"Thuộc" yêu cầu ≥3 lần nhớ liên tiếp và khoảng ôn ≥21 ngày — không bao giờ sau 1 lần trả lời.</p>
        </Panel>
        <Panel title="Chất lượng dữ liệu">
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Từ vựng cần duyệt</dt><dd className="tabular-nums font-medium">{d.vocabulary_by_status.needs_review ?? 0}</dd>
            <dt className="text-slate-500">Từ vựng chưa xác minh</dt><dd className="tabular-nums font-medium">{d.vocabulary_by_status.normalized ?? 0}</dd>
            <dt className="text-slate-500">Câu hỏi đề mẫu cần duyệt</dt><dd className="tabular-nums font-medium">{d.questions_by_status.needs_review ?? 0}</dd>
            <dt className="text-slate-500">Vấn đề mở (lỗi / cảnh báo)</dt><dd className="tabular-nums font-medium">{d.open_issues.error ?? 0} / {d.open_issues.warning ?? 0}</dd>
          </dl>
          <a href="#/review" className="mt-3 inline-block text-sm text-indigo-600 hover:underline dark:text-indigo-300">Mở màn hình duyệt →</a>
        </Panel>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Thi thử" action={<a href="#/exam" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">Mở trang thi →</a>}>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Lượt đã nộp</dt><dd className="tabular-nums font-medium">{d.exam.attempts_submitted}</dd>
            <dt className="text-slate-500">Lượt gần nhất</dt>
            <dd className="font-medium">{d.exam.last
              ? <a href={`#/exam?id=${d.exam.last.attempt_id}`} className="hover:underline">{d.exam.last.correct}/{d.exam.last.total} câu ({d.exam.last.accuracy ?? 0}%)</a>
              : 'Chưa có'}</dd>
            <dt className="text-slate-500">Câu sai chờ ôn</dt><dd className="tabular-nums font-medium">{d.exam.mistakes_pending}</dd>
            <dt className="text-slate-500">Ngân hàng câu hỏi</dt><dd className="tabular-nums font-medium">{d.exam.bank_questions}</dd>
          </dl>
        </Panel>
        <Panel title="Kiến thức N5 đã xác minh">
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {([['Từ vựng', d.vocabulary_by_status, '#/vocabulary'], ['Ngữ pháp', d.grammar_by_status, '#/grammar'],
              ['Kanji', d.kanji_by_status, '#/kanji']] as const).map(([l, m, href]) => (
              <div key={l} className="contents">
                <dt><a href={href} className="text-slate-500 hover:underline">{l}</a></dt>
                <dd className="tabular-nums font-medium">{m.verified ?? 0}/{Object.values(m).reduce((a, b) => a + b, 0)}</dd>
              </div>))}
          </dl>
        </Panel>
      </div>

      <Panel title="Bài có tỉ lệ quên cao nhất">
        {d.weak_lessons.length === 0
          ? <p className="text-sm text-slate-500">Chưa đủ dữ liệu: cần có lượt trả lời "Lại" trong phần ôn tập.</p>
          : <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
            {d.weak_lessons.map(w => (
              <li key={w.deck} className="flex items-center justify-between py-1.5">
                <span>{w.lesson_number ? `Bài ${w.lesson_number}` : w.deck}</span>
                <span className="tabular-nums text-slate-500">quên {w.wrong} / {w.wrong + w.right} lượt</span>
              </li>
            ))}
          </ul>}
      </Panel>
    </div>
  )
}
