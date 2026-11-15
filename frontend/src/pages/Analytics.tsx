import { useEffect, useState } from 'react'
import { api, type Analytics as A } from '../api'
import { ErrorBox, fmtDuration, Loading, Panel, StartButton } from '../ui'
import { BucketTable, MONDAI_LABEL, SECTION_LABEL } from './Exam'

const ENTITY_LABEL = { vocabulary: 'Từ vựng', grammar: 'Ngữ pháp', kanji: 'Kanji' } as const
const dm = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular-nums">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  )
}

/** Single-series column chart: study events per day. Hover/focus a column for its numbers. */
function DailyChart({ daily }: { daily: A['daily'] }) {
  const [sel, setSel] = useState(daily.length - 1)
  const n = (d: A['daily'][number]) => d.reviews + d.answers
  const max = Math.max(1, ...daily.map(n))
  const s = daily[sel]
  return (
    <div>
      <p className="mb-2 text-sm" aria-live="polite">
        <b>{dm(s.date)}</b>: {n(s)} lượt ({s.reviews} ôn thẻ, nhớ {s.reviews_correct}; {s.answers} câu hỏi) · {fmtDuration(s.seconds)}
      </p>
      <div className="relative">
        <div className="absolute inset-x-0 top-0 border-t border-dashed border-slate-200 dark:border-slate-700" />
        <span className="absolute -top-2 right-0 bg-white px-1 text-[10px] tabular-nums text-slate-500 dark:bg-slate-900">{max}</span>
        <div className="flex h-36 items-end gap-0.5 border-b border-slate-300 dark:border-slate-600"
          role="img" aria-label={`Lượt học mỗi ngày, ${daily.length} ngày gần nhất, cao nhất ${max}`}>
          {daily.map((d, i) => (
            <div key={d.date} tabIndex={0} onMouseEnter={() => setSel(i)} onFocus={() => setSel(i)}
              aria-label={`${dm(d.date)}: ${n(d)} lượt`}
              className="group flex h-full flex-1 cursor-default items-end outline-none">
              <div className={`w-full rounded-t ${i === sel ? 'bg-indigo-700 dark:bg-indigo-300' : 'bg-indigo-500 group-hover:bg-indigo-600'}`}
                style={{ height: n(d) ? `${Math.max(2, (n(d) / max) * 100)}%` : 0 }} />
            </div>))}
        </div>
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-slate-500">
        <span>{dm(daily[0].date)}</span><span>Hôm nay</span>
      </div>
    </div>
  )
}

export default function Analytics() {
  const [a, setA] = useState<A | null>(null)
  const [err, setErr] = useState<unknown>(null)
  useEffect(() => { api.analytics().then(setA).catch(setErr) }, [])
  if (err) return <ErrorBox error={err} />
  if (!a) return <Loading />

  const activeDays = a.daily.filter(d => d.reviews + d.answers).length
  const sections = ['vocabulary', 'grammar_reading', 'listening']
  const ret = Object.values(a.srs_retention)
  const srsN = ret.reduce((x, r) => x + r.reviews, 0)
  const srsOk = ret.reduce((x, r) => x + r.remembered, 0)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Thống kê học tập</h1>
        <p className="text-sm text-slate-500">
          Tính từ lượt ôn thẻ SRS và câu trả lời trong thi thử/luyện tập. Thời gian là <b>ước tính</b>: cộng khoảng cách giữa
          hai lần trả lời liên tiếp nếu ≤ 5 phút.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Tổng thời gian học" value={fmtDuration(a.study_seconds_total)} />
        <Stat label="30 ngày gần nhất" value={fmtDuration(a.study_seconds_period)} hint={`${activeDays}/30 ngày có học`} />
        <Stat label="Nhớ đúng thẻ SRS (30 ngày)" value={srsN ? `${Math.round((srsOk / srsN) * 1000) / 10}%` : '—'}
          hint={srsN ? `${srsOk}/${srsN} lượt ôn` : 'Chưa ôn'} />
        <Stat label="Lượt thi/luyện tập đã nộp" value={String(a.attempts.length)} hint="Tối đa 30 lượt gần nhất" />
      </div>

      <Panel title="Lượt học mỗi ngày (30 ngày)">
        {activeDays ? <DailyChart daily={a.daily} />
          : <p className="text-sm text-slate-500">Chưa có hoạt động trong 30 ngày: hãy <a href="#/flashcards" className="text-indigo-600 hover:underline dark:text-indigo-300">ôn thẻ</a> hoặc <a href="#/exam" className="text-indigo-600 hover:underline dark:text-indigo-300">làm bài</a>.</p>}
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Nhớ đúng theo loại thẻ (30 ngày)">
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-slate-500"><tr><th className="py-1"></th><th className="text-right">Lượt</th><th className="text-right">Nhớ</th><th className="text-right">%</th></tr></thead>
            <tbody>{(Object.keys(ENTITY_LABEL) as (keyof typeof ENTITY_LABEL)[]).map(e => {
              const r = a.srs_retention[e]
              return <tr key={e} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1"><a href={`#/flashcards?entity=${e}`} className="hover:underline">{ENTITY_LABEL[e]}</a></td>
                <td className="text-right tabular-nums">{r?.reviews ?? 0}</td><td className="text-right tabular-nums">{r?.remembered ?? 0}</td>
                <td className="text-right tabular-nums">{r?.retention ?? '—'}</td></tr>
            })}</tbody>
          </table>
          <p className="mt-2 text-xs text-slate-500">"Nhớ" = mọi đánh giá trừ "Lại".</p>
        </Panel>
        <Panel title="Độ chính xác theo phần (lần trả lời gần nhất mỗi câu)">
          {Object.keys(a.by_section).length
            ? <BucketTable title="" rows={Object.entries(a.by_section).map(([k, b]) => [SECTION_LABEL[k] ?? k, b])} />
            : <p className="text-sm text-slate-500">Chưa nộp lượt thi/luyện tập nào.</p>}
        </Panel>
      </div>

      <Panel title="Lịch sử thi theo thời gian" action={<a href="#/exam" className="text-sm text-indigo-600 hover:underline dark:text-indigo-300">Trang thi →</a>}>
        {a.attempts.length === 0 ? <p className="text-sm text-slate-500">Chưa nộp lượt nào.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-slate-500">
                <tr><th className="py-1">Ngày</th><th>Lượt</th><th className="text-right">Câu</th><th className="text-right">Chung %</th>
                  {sections.map(s => <th key={s} className="text-right">{SECTION_LABEL[s]} %</th>)}</tr>
              </thead>
              <tbody>{[...a.attempts].reverse().map(t => (
                <tr key={t.attempt_id} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="whitespace-nowrap py-1 pr-2 tabular-nums">{dm(t.submitted_at)}</td>
                  <td className="pr-2"><a href={`#/exam?id=${t.attempt_id}`} className="hover:underline">{t.title}</a></td>
                  <td className="text-right tabular-nums">{t.total}</td>
                  <td className="text-right font-medium tabular-nums">{t.accuracy ?? '—'}</td>
                  {sections.map(s => <td key={s} className="text-right tabular-nums">{t.by_section[s] ?? '—'}</td>)}
                </tr>))}</tbody>
            </table>
          </div>)}
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel title="Dạng câu yếu (Mondai)">
          {a.by_mondai.filter(m => m.correct < m.total).length === 0
            ? <p className="text-sm text-slate-500">Chưa có dạng câu nào còn sai.</p>
            : <BucketTable title="" rows={[...a.by_mondai].filter(m => m.correct < m.total)
              .sort((x, y) => (x.accuracy ?? 0) - (y.accuracy ?? 0)).slice(0, 8)
              .map(b => [MONDAI_LABEL[b.mondai_type ?? ''] ?? b.mondai_type ?? `もんだい${b.mondai_no}`, b])} />}
        </Panel>
        <Panel title="Điểm ngữ pháp yếu">
          {a.weak_grammar_points.length === 0
            ? <p className="text-sm text-slate-500">Chưa có: làm câu 文の文法 để biết điểm nào còn sai.</p>
            : <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
              {a.weak_grammar_points.map(w => (
                <li key={w.grammar_id} className="flex items-center justify-between gap-2 py-1.5">
                  <a href={`#/grammar?id=${w.grammar_id}`} className="jp hover:underline">{w.pattern ?? w.grammar_id}</a>
                  <span className="flex shrink-0 items-center gap-2"><span className="tabular-nums text-slate-500">đúng {w.correct}/{w.total}</span>
                    <StartButton body={{ mode: 'practice', grammar_id: w.grammar_id, limit: 10 }}>Luyện</StartButton></span>
                </li>))}
            </ul>}
        </Panel>
      </div>

      <Panel title="Câu sai lặp lại (sai ≥ 2 lần)"
        action={a.repeated_mistakes.length ? <StartButton body={{ mode: 'practice', mistakes_only: true, limit: 200 }}>Ôn câu sai</StartButton> : undefined}>
        {a.repeated_mistakes.length === 0
          ? <p className="text-sm text-slate-500">Chưa có câu nào sai từ 2 lần trở lên.</p>
          : <ul className="divide-y divide-slate-100 text-sm dark:divide-slate-800">
            {a.repeated_mistakes.map(m => (
              <li key={m.question_id} className="flex items-center justify-between gap-2 py-1.5">
                <span className="min-w-0">
                  <span className="jp block truncate">{m.question_text || m.question_id}</span>
                  <span className="text-xs text-slate-500">{SECTION_LABEL[m.section] ?? m.section}
                    {m.mondai_type ? ` · ${MONDAI_LABEL[m.mondai_type] ?? m.mondai_type}` : ''}
                    {m.grammar_id && <> · <a href={`#/grammar?id=${m.grammar_id}`} className="jp hover:underline">{m.grammar_pattern ?? m.grammar_id}</a></>}
                  </span>
                </span>
                <span className="shrink-0 tabular-nums text-rose-600 dark:text-rose-300">sai {m.wrong} lần</span>
              </li>))}
          </ul>}
        <p className="mt-2 text-xs text-slate-500">"Ôn câu sai" lấy các câu có lần trả lời gần nhất còn sai (câu đã làm đúng lại sẽ không vào lượt ôn).</p>
      </Panel>
    </div>
  )
}
